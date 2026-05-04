from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .admin_site import admin_site
from .models import Cart, CartItem, Category, Order, OrderItem, Product, UserProfile


def _user_role(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None)


def _is_order_staff(user):
    return bool(user.is_superuser or user.is_staff or _user_role(user) in {UserProfile.ROLE_STAFF, UserProfile.ROLE_MANAGER})


def _is_order_manager(user):
    return bool(user.is_superuser or _user_role(user) == UserProfile.ROLE_MANAGER)


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product, site=admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "description", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    list_select_related = ("category",)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.orderitem_set.exists():
            return False
        return super().has_delete_permission(request, obj=obj)

    def delete_queryset(self, request, queryset):
        blocked = queryset.filter(orderitem__isnull=False).distinct()
        allowed = queryset.exclude(pk__in=blocked.values_list("pk", flat=True))
        if blocked.exists():
            messages.error(request, "Có sản phẩm đã phát sinh giao dịch nên không thể xóa. Hãy chuyển sang ẩn sản phẩm (tắt hiển thị) thay vì xóa.")
        if allowed.exists():
            super().delete_queryset(request, allowed)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart, site=admin_site)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    inlines = [CartItemInline]
    search_fields = ("user__username", "user__email")
    list_select_related = ("user",)


@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "tracking_code", "user", "full_name", "payment_method", "payment_status", "order_status", "total_amount", "created_at")
    list_filter = ("payment_method", "payment_status", "order_status", "created_at")
    search_fields = ("full_name", "phone", "email")
    list_select_related = ("user",)
    actions = ["mark_paid", "mark_confirmed", "mark_shipping", "mark_completed", "mark_cancelled"]

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
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "unit_price", "quantity", "line_total")
    search_fields = ("product_name",)


@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
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
