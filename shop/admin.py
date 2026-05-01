from django.contrib import admin
from django.utils import timezone

from .models import Cart, CartItem, Category, Order, OrderItem, Product, UserProfile


def _user_role(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None)


def _is_order_staff(user):
    return bool(user.is_superuser or user.is_staff or _user_role(user) in {UserProfile.ROLE_STAFF, UserProfile.ROLE_MANAGER})


def _is_order_manager(user):
    return bool(user.is_superuser or _user_role(user) == UserProfile.ROLE_MANAGER)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "description", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    list_select_related = ("category",)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    inlines = [CartItemInline]
    search_fields = ("user__username", "user__email")
    list_select_related = ("user",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "tracking_code", "user", "full_name", "payment_method", "payment_status", "order_status", "total_amount", "created_at")
    list_filter = ("payment_method", "payment_status", "order_status", "created_at")
    search_fields = ("full_name", "phone", "email")
    list_select_related = ("user",)
    actions = ["mark_confirmed", "mark_shipping", "mark_completed", "mark_cancelled"]

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
            actions.pop("mark_completed", None)
            actions.pop("mark_cancelled", None)
        return actions

    @admin.action(description="Đánh dấu đã xác nhận")
    def mark_confirmed(self, request, queryset):
        queryset.update(order_status="CONFIRMED", confirmed_at=timezone.now())

    @admin.action(description="Đánh dấu đang giao")
    def mark_shipping(self, request, queryset):
        now = timezone.now()
        queryset.update(order_status="SHIPPING", confirmed_at=now, shipping_at=now)

    @admin.action(description="Đánh dấu hoàn tất")
    def mark_completed(self, request, queryset):
        now = timezone.now()
        queryset.update(order_status="COMPLETED", confirmed_at=now, shipping_at=now, completed_at=now)

    @admin.action(description="Đánh dấu đã hủy")
    def mark_cancelled(self, request, queryset):
        queryset.update(order_status="CANCELLED", cancelled_at=timezone.now())


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "unit_price", "quantity", "line_total")
    search_fields = ("product_name",)


@admin.register(UserProfile)
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
