from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .forms import LoginForm

urlpatterns = [
    path("", views.home_view, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("register/", views.register_view, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=LoginForm), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/tracking/", views.order_tracking, name="order_tracking"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/<int:order_id>/payment/", views.order_payment, name="order_payment"),
    path("orders/<int:order_id>/payment/cancel/", views.order_payment_cancel, name="order_payment_cancel"),
    path("payments/sandbox/<str:method>/<int:order_id>/", views.payment_sandbox, name="payment_sandbox"),
    path("payments/vnpay/return/", views.vnpay_return, name="vnpay_return"),
    path("payments/vnpay/ipn/", views.vnpay_ipn, name="vnpay_ipn"),
    path("api/address-suggestions/", views.address_suggestions, name="address_suggestions"),
    path("api/location-lookup/", views.address_suggestions, name="location_lookup"),
    path("cart/", views.view_cart, name="view_cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/item/<int:item_id>/<str:action>/", views.update_cart_item, name="update_cart_item"),
    path("checkout/", views.checkout, name="checkout"),
]
