from django.contrib import admin
from django.contrib import messages
from django import forms
from django.db import models
from django.db import transaction
from django.utils.html import format_html
from django.utils import timezone

from unfold.admin import ModelAdmin, TabularInline

from .admin_site import admin_site
from .models import Cart, CartItem, Category, Order, OrderItem, Product, UserProfile


def _user_role(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None)


def _is_order_staff(user):
    return bool(user.is_superuser or user.is_staff or _user_role(user) in {UserProfile.ROLE_STAFF, UserProfile.ROLE_MANAGER})


def _is_order_manager(user):
    return bool(user.is_superuser or _user_role(user) == UserProfile.ROLE_MANAGER)


def _format_vnd(value):
    amount = int((value or 0))
    return f"{amount:,}".replace(",", ".") + " ₫"


def _badge(label, tone):
    tone_classes = {
        "price": "bg-primary-600 text-white",
        "primary": "bg-primary-100 text-primary-700 dark:bg-primary-950/40 dark:text-primary-200",
        "success": "bg-success-100 text-success-800 dark:bg-success-950/40 dark:text-success-200",
        "warning": "bg-warning-100 text-warning-800 dark:bg-warning-950/40 dark:text-warning-200",
        "danger": "bg-danger-100 text-danger-800 dark:bg-danger-950/40 dark:text-danger-200",
        "info": "bg-info-100 text-info-800 dark:bg-info-950/40 dark:text-info-200",
        "muted": "bg-base-100 text-base-700 dark:bg-base-800 dark:text-base-200",
    }
    classes = tone_classes.get(tone, tone_classes["primary"])
    return format_html(
        '<span class="inline-flex items-center whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold {}">{}</span>',
        classes,
        label,
    )


class ZenithModelAdmin(ModelAdmin):
    list_filter_sheet = True
    list_fullwidth = True


class ZenithTabularInline(TabularInline):
    extra = 0


@admin.register(Category, site=admin_site)
class CategoryAdmin(ZenithModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product, site=admin_site)
class ProductAdmin(ZenithModelAdmin):
    list_display = ("name", "category", "price_badge", "stock_badge", "active_badge", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "description", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    list_select_related = ("category",)
    fieldsets = (
        ("Thông tin sản phẩm", {"fields": ("category", "name", "slug", "description")}),
        ("Giá và tồn kho", {"fields": ("price", "stock", "is_active")}),
        ("Hình ảnh", {"fields": ("image",)}),
        ("Hệ thống", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at", "updated_at")
    formfield_overrides = {models.TextField: {"widget": forms.Textarea(attrs={"rows": 5})}}

    @admin.display(description="Giá")
    def price_badge(self, obj):
        return _badge(_format_vnd(obj.price), "price")

    @admin.display(description="Tồn kho")
    def stock_badge(self, obj):
        tone = "danger" if obj.stock <= 0 else "warning" if obj.stock <= 10 else "success"
        return _badge(str(obj.stock), tone)

    @admin.display(description="Trạng thái")
    def active_badge(self, obj):
        return _badge("Đang hiển thị" if obj.is_active else "Đã ẩn", "success" if obj.is_active else "muted")

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.orderitem_set.exists():
            return False
        return super().has_delete_permission(request, obj=obj)

    def delete_queryset(self, request, queryset):
        blocked = queryset.filter(orderitem__isnull=False).distinct()
        allowed = queryset.exclude(pk__in=blocked.values_list("pk", flat=True))
        if blocked.exists():
            messages.error(request, "Có sản phẩm đã phát sinh giao dịch nên chưa thể xóa. Bạn có thể ẩn sản phẩm để giữ lịch sử bán hàng.")
        if allowed.exists():
            super().delete_queryset(request, allowed)


class CartItemInline(ZenithTabularInline):
    model = CartItem


class OrderItemInline(ZenithTabularInline):
    model = OrderItem
    can_delete = False
    fields = ("product_name", "unit_price", "quantity", "line_total")
    readonly_fields = fields


@admin.register(Cart, site=admin_site)
class CartAdmin(ZenithModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    inlines = [CartItemInline]
    search_fields = ("user__username", "user__email")
    list_select_related = ("user",)


@admin.register(Order, site=admin_site)
class OrderAdmin(ZenithModelAdmin):
    list_display = ("tracking_badge", "customer_badge", "payment_badge", "status_badge", "total_badge", "created_at")
    list_filter = ("payment_method", "payment_status", "order_status", "created_at")
    search_fields = ("full_name", "phone", "email")
    list_select_related = ("user",)
    actions = ["mark_paid", "mark_confirmed", "mark_shipping", "mark_completed", "mark_cancelled"]
    inlines = [OrderItemInline]
    fieldsets = (
        ("Khách hàng", {"fields": ("user", "full_name", "phone", "email")}),
        ("Giao hàng", {"fields": ("shipping_address", "province", "district", "ward", "street_address", "delivery_place_name", "delivery_latitude", "delivery_longitude")}),
        ("Thanh toán", {"fields": ("payment_method", "payment_status", "subtotal", "shipping_fee", "total_amount")}),
        ("Xử lý đơn", {"fields": ("order_status", "tracking_code", "note", "confirmed_at", "shipping_at", "completed_at", "cancelled_at", "customer_payment_notified_at")}),
        ("Hệ thống", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def has_module_permission(self, request):
        return _is_order_staff(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_order_staff(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return _is_order_staff(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_order_manager(request.user)

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in Order._meta.fields)

    @admin.display(description="Mã đơn")
    def tracking_badge(self, obj):
        return _badge(obj.display_tracking_code, "muted")

    @admin.display(description="Khách hàng")
    def customer_badge(self, obj):
        return format_html(
            '<div class="flex flex-col items-start gap-0.5"><strong class="text-sm font-semibold text-base-950 dark:text-base-50">{}</strong><span class="text-xs text-font-subtle-light dark:text-font-subtle-dark">{}</span></div>',
            obj.full_name,
            obj.phone,
        )

    @admin.display(description="Thanh toán")
    def payment_badge(self, obj):
        tone = "success" if obj.payment_status == Order.PAYMENT_PAID else "warning" if obj.payment_status == Order.PAYMENT_PENDING else "danger"
        return _badge(obj.get_payment_status_display(), tone)

    @admin.display(description="Trạng thái")
    def status_badge(self, obj):
        tone_map = {
            Order.STATUS_PENDING: "warning",
            Order.STATUS_CONFIRMED: "info",
            Order.STATUS_SHIPPING: "primary",
            Order.STATUS_COMPLETED: "success",
            Order.STATUS_CANCELLED: "danger",
        }
        return _badge(obj.get_order_status_display(), tone_map.get(obj.order_status, "muted"))

    @admin.display(description="Tổng tiền")
    def total_badge(self, obj):
        return _badge(_format_vnd(obj.total_amount), "price")

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not _is_order_manager(request.user):
            actions.pop("mark_paid", None)
            actions.pop("mark_completed", None)
            actions.pop("mark_cancelled", None)
        return actions

    def _requires_paid_for_shipping(self, order):
        return order.is_online_payment and order.payment_status != Order.PAYMENT_PAID

    @admin.action(description="Đánh dấu đã thanh toán (đối soát xong)")
    def mark_paid(self, request, queryset):
        with transaction.atomic():
            locked = queryset.select_for_update()
            updated = 0
            skipped = 0
            for order in locked:
                if order.payment_status == Order.PAYMENT_PAID:
                    skipped += 1
                    continue
                if order.order_status == Order.STATUS_CANCELLED:
                    skipped += 1
                    continue
                order.payment_status = Order.PAYMENT_PAID
                order.order_status = Order.STATUS_CONFIRMED
                order.confirmed_at = order.confirmed_at or timezone.now()
                order.save(update_fields=["payment_status", "order_status", "confirmed_at", "updated_at"])
                updated += 1
        if updated:
            messages.success(request, f"Đã cập nhật thanh toán cho {updated} đơn hàng.")
        if skipped and not updated:
            messages.info(request, "Không có đơn hàng phù hợp để cập nhật.")

    @admin.action(description="Đánh dấu đã xác nhận")
    def mark_confirmed(self, request, queryset):
        with transaction.atomic():
            locked = queryset.select_for_update()
            updated = 0
            skipped = 0
            for order in locked:
                if order.order_status == Order.STATUS_CANCELLED:
                    skipped += 1
                    continue
                if order.is_online_payment and order.payment_status != Order.PAYMENT_PAID:
                    skipped += 1
                    continue
                order.mark_status(Order.STATUS_CONFIRMED)
                updated += 1
        if updated:
            messages.success(request, f"Đã xác nhận {updated} đơn hàng.")
        if skipped and not updated:
            messages.info(request, "Không có đơn hàng phù hợp để xác nhận.")

    @admin.action(description="Đánh dấu đang giao")
    def mark_shipping(self, request, queryset):
        with transaction.atomic():
            locked = queryset.select_for_update()
            updated = 0
            skipped = 0
            for order in locked:
                if order.order_status == Order.STATUS_CANCELLED:
                    skipped += 1
                    continue
                if self._requires_paid_for_shipping(order):
                    skipped += 1
                    continue
                order.mark_status(Order.STATUS_SHIPPING)
                updated += 1
        if updated:
            messages.success(request, f"Đã chuyển {updated} đơn hàng sang trạng thái đang giao.")
        if skipped and not updated:
            messages.info(request, "Không có đơn hàng phù hợp để cập nhật.")

    @admin.action(description="Đánh dấu hoàn tất")
    def mark_completed(self, request, queryset):
        with transaction.atomic():
            locked = queryset.select_for_update()
            updated = 0
            skipped = 0
            for order in locked:
                if order.order_status == Order.STATUS_CANCELLED:
                    skipped += 1
                    continue
                if self._requires_paid_for_shipping(order):
                    skipped += 1
                    continue
                order.mark_status(Order.STATUS_COMPLETED)
                updated += 1
        if updated:
            messages.success(request, f"Đã hoàn tất {updated} đơn hàng.")
        if skipped and not updated:
            messages.info(request, "Không có đơn hàng phù hợp để cập nhật.")

    @admin.action(description="Đánh dấu đã hủy")
    def mark_cancelled(self, request, queryset):
        with transaction.atomic():
            locked = queryset.select_for_update()
            updated = 0
            skipped = 0
            for order in locked:
                if order.payment_status == Order.PAYMENT_PAID:
                    skipped += 1
                    continue
                if order.order_status == Order.STATUS_COMPLETED:
                    skipped += 1
                    continue
                if order.order_status == Order.STATUS_CANCELLED:
                    skipped += 1
                    continue
                order.mark_status(Order.STATUS_CANCELLED)
                updated += 1
        if updated:
            messages.success(request, f"Đã hủy {updated} đơn hàng và hoàn kho.")
        if skipped and not updated:
            messages.info(request, "Không có đơn hàng phù hợp để hủy.")


@admin.register(OrderItem, site=admin_site)
class OrderItemAdmin(ZenithModelAdmin):
    list_display = ("order", "product_name", "unit_price", "quantity", "line_total")
    search_fields = ("product_name",)


@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(ZenithModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")

    def has_module_permission(self, request):
        return request.user.is_superuser or _user_role(request.user) == UserProfile.ROLE_MANAGER

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or _user_role(request.user) == UserProfile.ROLE_MANAGER

    def has_add_permission(self, request):
        return request.user.is_superuser or _user_role(request.user) == UserProfile.ROLE_MANAGER

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or _user_role(request.user) == UserProfile.ROLE_MANAGER

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or _user_role(request.user) == UserProfile.ROLE_MANAGER
