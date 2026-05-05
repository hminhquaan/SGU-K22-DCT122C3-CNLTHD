from decimal import Decimal
import hashlib
import json
import hmac
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from shop.admin_site import admin_site
from shop.admin import OrderAdmin, UserProfileAdmin
from shop.forms import CheckoutForm, RegisterForm
from shop.models import Cart, CartItem, Category, Order, OrderItem, Product, UserProfile


class ShopModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Yoga", description="Dụng cụ yoga")
        self.product = Product.objects.create(
            category=self.category,
            name="Yoga Mat",
            price=Decimal("350000.00"),
            description="Thảm yoga",
            stock=10,
        )

    def test_category_slug_is_generated(self):
        self.assertEqual(self.category.slug, "yoga")

    def test_product_slug_is_generated(self):
        self.assertEqual(self.product.slug, "yoga-mat")

    def test_cart_subtotal(self):
        user = User.objects.create_user(username="tester", password="pass12345")
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.assertEqual(cart.subtotal, Decimal("700000.00"))

    def test_order_defaults(self):
        user = User.objects.create_user(username="buyer", password="pass12345")
        order = Order.objects.create(
            user=user,
            full_name="Buyer",
            phone="0901234567",
            email="buyer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("350000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("380000.00"),
        )
        self.assertEqual(order.payment_method, Order.METHOD_COD)
        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)
        self.assertEqual(order.order_status, Order.STATUS_PENDING)
        self.assertEqual(order.formatted_shipping_address, "123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh")

    def test_cannot_delete_product_after_transaction(self):
        user = User.objects.create_user(username="buyer", password="pass12345")
        order = Order.objects.create(
            user=user,
            full_name="Buyer",
            phone="0901234567",
            email="buyer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("350000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("380000.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=1,
            line_total=self.product.price,
        )

        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_cancelling_online_order_sets_payment_cancelled(self):
        user = User.objects.create_user(username="buyer2", password="pass12345")
        order = Order.objects.create(
            user=user,
            full_name="Buyer",
            phone="0901234567",
            email="buyer2@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("350000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("380000.00"),
            payment_method=Order.METHOD_BANK_TRANSFER,
            payment_status=Order.PAYMENT_PENDING,
            order_status=Order.STATUS_PENDING,
        )

        order.mark_status(Order.STATUS_CANCELLED)
        order.refresh_from_db()
        self.assertEqual(order.order_status, Order.STATUS_CANCELLED)
        self.assertEqual(order.payment_status, Order.PAYMENT_CANCELLED)

    def test_cancelling_cod_order_keeps_payment_pending(self):
        user = User.objects.create_user(username="buyer3", password="pass12345")
        order = Order.objects.create(
            user=user,
            full_name="Buyer",
            phone="0901234567",
            email="buyer3@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("350000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("380000.00"),
            payment_method=Order.METHOD_COD,
            payment_status=Order.PAYMENT_PENDING,
            order_status=Order.STATUS_PENDING,
        )

        order.mark_status(Order.STATUS_CANCELLED)
        order.refresh_from_db()
        self.assertEqual(order.order_status, Order.STATUS_CANCELLED)
        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)

    def test_completed_cod_order_marks_paid(self):
        user = User.objects.create_user(username="buyer4", password="pass12345")
        order = Order.objects.create(
            user=user,
            full_name="Buyer",
            phone="0901234567",
            email="buyer4@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("350000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("380000.00"),
            payment_method=Order.METHOD_COD,
            payment_status=Order.PAYMENT_PENDING,
            order_status=Order.STATUS_SHIPPING,
        )

        order.mark_status(Order.STATUS_COMPLETED)
        order.refresh_from_db()
        self.assertEqual(order.order_status, Order.STATUS_COMPLETED)
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)


class ShopFormTests(TestCase):
    def test_checkout_form_rejects_short_phone(self):
        form = CheckoutForm(
            data={
                "full_name": "A",
                "phone": "123",
                "email": "a@example.com",
                "province": "Hà Nội",
                "district": "Ba Đình",
                "ward": "Điện Biên",
                "street_address": "1 Tràng Thi",
                "payment_method": "COD",
                "note": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_register_form_rejects_duplicate_email(self):
        User.objects.create_user(username="existing", email="test@example.com", password="pass12345")
        form = RegisterForm(
            data={
                "username": "newuser",
                "first_name": "",
                "last_name": "",
                "email": "test@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_register_form_creates_customer_profile(self):
        form = RegisterForm(
            data={
                "username": "newcustomer",
                "first_name": "",
                "last_name": "",
                "email": "newcustomer@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.profile.role, UserProfile.ROLE_CUSTOMER)


class ShopViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Gym", description="Gym gear")
        self.product = Product.objects.create(
            category=self.category,
            name="Dumbbell",
            price=Decimal("500000.00"),
            description="Tạ tay",
            stock=5,
        )
        self.user = User.objects.create_user(username="customer", password="pass12345", email="customer@example.com")

    def test_product_list_page_loads(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)

    def test_product_detail_page_loads(self):
        response = self.client.get(reverse("product_detail", args=[self.product.slug]))
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart_requires_login(self):
        response = self.client.post(reverse("add_to_cart", args=[self.product.id]), data={"quantity": 1})
        self.assertEqual(response.status_code, 302)

    def test_checkout_creates_order(self):
        self.client.login(username="customer", password="pass12345")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        response = self.client.post(
            reverse("checkout"),
            data={
                "full_name": "Customer",
                "phone": "0901234567",
                "email": "customer@example.com",
                "province": "TP. Hồ Chí Minh",
                "district": "Quận 1",
                "ward": "Bến Nghé",
                "street_address": "123 Lê Lợi",
                "payment_method": "BANK_TRANSFER",
                "note": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertTrue(order.tracking_code.startswith("ZF"))

    def test_order_tracking_redirects_to_orders_lookup(self):
        self.client.login(username="customer", password="pass12345")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.post(
            reverse("checkout"),
            data={
                "full_name": "Customer",
                "phone": "0901234567",
                "email": "customer@example.com",
                "province": "TP. Hồ Chí Minh",
                "district": "Quận 1",
                "ward": "Bến Nghé",
                "street_address": "123 Lê Lợi",
                "payment_method": "BANK_TRANSFER",
                "note": "",
            },
        )
        order = Order.objects.get()
        response = self.client.get(reverse("order_tracking"), data={"tracking_code": order.tracking_code})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("order_list"), response["Location"])

    def test_guest_can_lookup_order_with_email(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
        )

        self.client.logout()
        response = self.client.get(
            reverse("order_list"),
            data={"tracking_code": order.display_tracking_code, "contact": "customer@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["focused_order"].id, order.id)

    def test_manual_payment_confirmation_marks_paid(self):
        self.client.login(username="customer", password="pass12345")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        response = self.client.post(
            reverse("checkout"),
            data={
                "full_name": "Customer",
                "phone": "0901234567",
                "email": "customer@example.com",
                "province": "TP. Hồ Chí Minh",
                "district": "Quận 1",
                "ward": "Bến Nghé",
                "street_address": "123 Lê Lợi",
                "payment_method": "BANK_TRANSFER",
                "note": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)
        self.assertIsNone(order.customer_payment_notified_at)

        response = self.client.post(reverse("order_payment", args=[order.id]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)
        self.assertEqual(order.order_status, Order.STATUS_CONFIRMED)
        self.assertIsNotNone(order.customer_payment_notified_at)

    def test_checkout_persists_shipping_fee(self):
        self.client.login(username="customer", password="pass12345")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        self.client.post(
            reverse("checkout"),
            data={
                "full_name": "Customer",
                "phone": "0901234567",
                "email": "customer@example.com",
                "province": "TP. Hồ Chí Minh",
                "district": "Quận 1",
                "ward": "Bến Nghé",
                "street_address": "123 Lê Lợi",
                "payment_method": "COD",
                "note": "",
            },
        )
        order = Order.objects.get()
        self.assertEqual(order.shipping_fee, Decimal("30000.00"))

    def test_momo_payment_page_exposes_sandbox_url(self):
        self.client.login(username="customer", password="pass12345")
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_MOMO,
        )

        response = self.client.get(reverse("order_payment", args=[order.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/payments/sandbox/momo/", response["Location"])

    def test_sandbox_success_marks_order_paid(self):
        self.client.login(username="customer", password="pass12345")
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_MOMO,
        )
        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)

        response = self.client.post(reverse("payment_sandbox", args=["momo", order.id]), data={"action": "success"})
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)
        self.assertEqual(order.order_status, Order.STATUS_CONFIRMED)

    def test_sandbox_cancel_restores_stock(self):
        self.client.login(username="customer", password="pass12345")
        self.product.stock = 4
        self.product.save(update_fields=["stock"])
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_ZALOPAY,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            line_total=self.product.price,
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)

        response = self.client.post(reverse("payment_sandbox", args=["zalopay", order.id]), data={"action": "cancel"})
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_CANCELLED)
        self.assertEqual(order.order_status, Order.STATUS_CANCELLED)
        self.assertEqual(self.product.stock, 5)

    @patch("shop.views.urlopen")
    def test_address_suggestions_return_detailed_places(self, mock_urlopen):
        mock_payload = [
            {
                "display_name": "81 Trần Hưng Đạo, Phường Cầu Kho, Quận 1, TP. Hồ Chí Minh, Việt Nam",
                "name": "81 Trần Hưng Đạo",
                "class": "amenity",
                "type": "restaurant",
                "lat": "10.768000",
                "lon": "106.700000",
                "address": {
                    "house_number": "81",
                    "road": "Trần Hưng Đạo",
                    "quarter": "Cầu Kho",
                    "city_district": "Quận 1",
                    "state": "TP. Hồ Chí Minh",
                    "postcode": "700000",
                },
            }
        ]

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(mock_payload).encode("utf-8")

        mock_urlopen.return_value = FakeResponse()

        response = self.client.get(reverse("address_suggestions"), data={"q": "81 Trần Hưng Đạo"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        suggestion = payload["results"][0]
        self.assertEqual(suggestion["label"], "81 Trần Hưng Đạo")
        self.assertIn("Cầu Kho", suggestion["detail"])
        self.assertEqual(suggestion["lat"], "10.768000")
        self.assertEqual(suggestion["lon"], "106.700000")

    @override_settings(GOOGLE_MAPS_API_KEY="google-test-key")
    @patch("shop.views.urlopen")
    def test_address_suggestions_use_google_places(self, mock_urlopen):
        autocomplete_payload = {
            "status": "OK",
            "predictions": [
                {
                    "description": "81 Trần Hưng Đạo, Phường Cầu Kho, Quận 1, Hồ Chí Minh, Việt Nam",
                    "place_id": "place-123",
                    "types": ["street_address"],
                    "structured_formatting": {
                        "main_text": "81 Trần Hưng Đạo",
                        "secondary_text": "Phường Cầu Kho, Quận 1, Hồ Chí Minh, Việt Nam",
                    },
                }
            ],
        }

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout=4):
            if "autocomplete" in request.full_url:
                return FakeResponse(autocomplete_payload)
            raise AssertionError(f"Unexpected URL: {request.full_url}")

        mock_urlopen.side_effect = fake_urlopen

        response = self.client.get(reverse("address_suggestions"), data={"q": "81 Trần Hưng Đạo"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["results"][0]["provider"], "google")
        self.assertEqual(payload["results"][0]["label"], "81 Trần Hưng Đạo")
        self.assertIn("Phường Cầu Kho", payload["results"][0]["detail"])

    @override_settings(GOOGLE_MAPS_API_KEY="google-test-key")
    @patch("shop.views.urlopen")
    def test_address_suggestions_resolve_google_place_details(self, mock_urlopen):
        detail_payload = {
            "status": "OK",
            "result": {
                "name": "81 Trần Hưng Đạo",
                "formatted_address": "81 Trần Hưng Đạo, Phường Cầu Kho, Quận 1, Hồ Chí Minh, Việt Nam",
                "types": ["street_address"],
                "geometry": {"location": {"lat": 10.768, "lng": 106.7}},
                "address_components": [
                    {"long_name": "81", "short_name": "81", "types": ["street_number"]},
                    {"long_name": "Trần Hưng Đạo", "short_name": "Trần Hưng Đạo", "types": ["route"]},
                    {"long_name": "Phường Cầu Kho", "short_name": "Cầu Kho", "types": ["sublocality_level_1"]},
                    {"long_name": "Quận 1", "short_name": "Quận 1", "types": ["administrative_area_level_2"]},
                    {"long_name": "Hồ Chí Minh", "short_name": "Hồ Chí Minh", "types": ["administrative_area_level_1"]},
                    {"long_name": "700000", "short_name": "700000", "types": ["postal_code"]},
                ],
            },
        }

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout=4):
            if "details" in request.full_url:
                return FakeResponse(detail_payload)
            raise AssertionError(f"Unexpected URL: {request.full_url}")

        mock_urlopen.side_effect = fake_urlopen

        response = self.client.get(reverse("address_suggestions"), data={"place_id": "place-123"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        suggestion = payload["results"][0]
        self.assertEqual(suggestion["street_address"], "81 Trần Hưng Đạo")
        self.assertEqual(suggestion["district"], "Quận 1")
        self.assertEqual(suggestion["province"], "TP. Hồ Chí Minh")
        self.assertEqual(suggestion["lat"], "10.768")
        self.assertEqual(suggestion["lon"], "106.7")

    def test_manager_role_sees_all_orders(self):
        Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
        )
        other_user = User.objects.create_user(username="other", password="pass12345", email="other@example.com")
        Order.objects.create(
            user=other_user,
            full_name="Other Customer",
            phone="0901234568",
            email="other@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="1 Nguyen Hue",
            shipping_address="1 Nguyen Hue, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
        )
        self.user.profile.role = UserProfile.ROLE_MANAGER
        self.user.profile.save(update_fields=["role"])

        self.client.login(username="customer", password="pass12345")
        response = self.client.get(reverse("order_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["orders"].count(), 2)

    @override_settings(
        VNPAY_URL="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
        VNPAY_TMN_CODE="TESTCODE",
        VNPAY_HASH_SECRET="secret-key",
    )
    def test_vnpay_payment_page_exposes_gateway_url(self):
        self.client.login(username="customer", password="pass12345")
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_VNPAY,
        )

        response = self.client.get(reverse("order_payment", args=[order.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?"))

    @override_settings(
        VNPAY_URL="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
        VNPAY_TMN_CODE="TESTCODE",
        VNPAY_HASH_SECRET="secret-key",
    )
    def test_vnpay_return_marks_order_paid(self):
        self.client.login(username="customer", password="pass12345")
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_VNPAY,
        )

        payload = {
            "vnp_Amount": "53000000",
            "vnp_Command": "pay",
            "vnp_CreateDate": "20240501120000",
            "vnp_CurrCode": "VND",
            "vnp_ExpireDate": "20240501121500",
            "vnp_IpAddr": "127.0.0.1",
            "vnp_Locale": "vn",
            "vnp_OrderInfo": f"Thanh toan don hang {order.display_tracking_code}",
            "vnp_OrderType": "other",
            "vnp_ResponseCode": "00",
            "vnp_ReturnUrl": "http://testserver/payments/vnpay/return/",
            "vnp_TmnCode": "TESTCODE",
            "vnp_TransactionStatus": "00",
            "vnp_TxnRef": order.display_tracking_code,
            "vnp_Version": "2.1.0",
        }
        sign_data = "&".join(f"{key}={payload[key]}" for key in sorted(payload))
        payload["vnp_SecureHash"] = hmac.new(b"secret-key", sign_data.encode("utf-8"), hashlib.sha512).hexdigest()

        response = self.client.get(reverse("vnpay_return"), data=payload)
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)
        self.assertEqual(order.order_status, Order.STATUS_CONFIRMED)

    @override_settings(
        VNPAY_URL="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
        VNPAY_TMN_CODE="TESTCODE",
        VNPAY_HASH_SECRET="secret-key",
    )
    def test_vnpay_cancel_restores_stock_and_marks_order_cancelled(self):
        self.client.login(username="customer", password="pass12345")
        self.product.stock = 4
        self.product.save(update_fields=["stock"])
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_VNPAY,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            line_total=self.product.price,
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)

        response = self.client.post(reverse("order_payment_cancel", args=[order.id]))
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_CANCELLED)
        self.assertEqual(order.order_status, Order.STATUS_CANCELLED)
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(order.user.cart.items.count(), 1)

    @override_settings(
        VNPAY_URL="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
        VNPAY_TMN_CODE="TESTCODE",
        VNPAY_HASH_SECRET="secret-key",
    )
    def test_vnpay_return_cancelled_marks_order_failed(self):
        self.client.login(username="customer", password="pass12345")
        self.product.stock = 4
        self.product.save(update_fields=["stock"])
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_VNPAY,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            line_total=self.product.price,
        )

        payload = {
            "vnp_Amount": "53000000",
            "vnp_Command": "pay",
            "vnp_CreateDate": "20240501120000",
            "vnp_CurrCode": "VND",
            "vnp_ExpireDate": "20240501121500",
            "vnp_IpAddr": "127.0.0.1",
            "vnp_Locale": "vn",
            "vnp_OrderInfo": f"Thanh toan don hang {order.display_tracking_code}",
            "vnp_OrderType": "other",
            "vnp_ResponseCode": "24",
            "vnp_ReturnUrl": "http://testserver/payments/vnpay/return/",
            "vnp_TmnCode": "TESTCODE",
            "vnp_TransactionStatus": "02",
            "vnp_TxnRef": order.display_tracking_code,
            "vnp_Version": "2.1.0",
        }
        sign_data = "&".join(f"{key}={payload[key]}" for key in sorted(payload))
        payload["vnp_SecureHash"] = hmac.new(b"secret-key", sign_data.encode("utf-8"), hashlib.sha512).hexdigest()

        response = self.client.get(reverse("vnpay_return"), data=payload)
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_CANCELLED)
        self.assertEqual(order.order_status, Order.STATUS_CANCELLED)
        self.assertEqual(self.product.stock, 5)

    @override_settings(
        VNPAY_URL="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
        VNPAY_TMN_CODE="TESTCODE",
        VNPAY_HASH_SECRET="secret-key",
    )
    def test_vnpay_ipn_confirms_paid_order(self):
        self.client.login(username="customer", password="pass12345")
        order = Order.objects.create(
            user=self.user,
            full_name="Customer",
            phone="0901234567",
            email="customer@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("500000.00"),
            shipping_fee=Decimal("30000.00"),
            total_amount=Decimal("530000.00"),
            payment_method=Order.METHOD_VNPAY,
        )

        payload = {
            "vnp_Amount": "53000000",
            "vnp_Command": "pay",
            "vnp_CreateDate": "20240501120000",
            "vnp_CurrCode": "VND",
            "vnp_ExpireDate": "20240501121500",
            "vnp_IpAddr": "127.0.0.1",
            "vnp_IpnUrl": "http://testserver/payments/vnpay/ipn/",
            "vnp_Locale": "vn",
            "vnp_OrderInfo": f"Thanh toan don hang {order.display_tracking_code}",
            "vnp_OrderType": "other",
            "vnp_ResponseCode": "00",
            "vnp_ReturnUrl": "http://testserver/payments/vnpay/return/",
            "vnp_TmnCode": "TESTCODE",
            "vnp_TransactionStatus": "00",
            "vnp_TxnRef": order.display_tracking_code,
            "vnp_Version": "2.1.0",
        }
        sign_data = "&".join(f"{key}={payload[key]}" for key in sorted(payload))
        payload["vnp_SecureHash"] = hmac.new(b"secret-key", sign_data.encode("utf-8"), hashlib.sha512).hexdigest()

        response = self.client.get(reverse("vnpay_ipn"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {"RspCode": "00", "Message": "Confirm Success"})
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)

    @override_settings(GOOGLE_MAPS_API_KEY="google-test-key")
    @patch("shop.views.urlopen")
    def test_location_lookup_returns_google_reverse_result(self, mock_urlopen):
        geocode_payload = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "81 Trần Hưng Đạo, Phường Cầu Kho, Quận 1, Hồ Chí Minh, Việt Nam",
                    "types": ["street_address"],
                    "geometry": {"location": {"lat": 10.768, "lng": 106.7}},
                    "address_components": [
                        {"long_name": "81", "short_name": "81", "types": ["street_number"]},
                        {"long_name": "Trần Hưng Đạo", "short_name": "Trần Hưng Đạo", "types": ["route"]},
                        {"long_name": "Phường Cầu Kho", "short_name": "Cầu Kho", "types": ["sublocality_level_1"]},
                        {"long_name": "Quận 1", "short_name": "Quận 1", "types": ["administrative_area_level_2"]},
                        {"long_name": "Hồ Chí Minh", "short_name": "Hồ Chí Minh", "types": ["administrative_area_level_1"]},
                    ],
                }
            ],
        }

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout=4):
            if "geocode" in request.full_url:
                return FakeResponse(geocode_payload)
            raise AssertionError(f"Unexpected URL: {request.full_url}")

        mock_urlopen.side_effect = fake_urlopen

        response = self.client.get(reverse("location_lookup"), data={"lat": "10.768", "lon": "106.7"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        suggestion = payload["results"][0]
        self.assertEqual(suggestion["provider"], "google")
        self.assertEqual(suggestion["street_address"], "81 Trần Hưng Đạo")
        self.assertEqual(suggestion["district"], "Quận 1")
        self.assertEqual(suggestion["province"], "TP. Hồ Chí Minh")


class ShopAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.order_admin = OrderAdmin(Order, admin.site)
        self.profile_admin = UserProfileAdmin(UserProfile, admin.site)

        self.staff_user = User.objects.create_user(username="staff", password="pass12345", is_staff=True)
        self.staff_user.profile.role = UserProfile.ROLE_STAFF
        self.staff_user.profile.save(update_fields=["role"])

        self.manager_user = User.objects.create_user(username="manager", password="pass12345", is_staff=True)
        self.manager_user.profile.role = UserProfile.ROLE_MANAGER
        self.manager_user.profile.save(update_fields=["role"])

    def _request_for(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return request

    def test_staff_sees_order_admin_but_not_role_admin(self):
        staff_request = self._request_for(self.staff_user)
        self.assertTrue(self.order_admin.has_view_permission(staff_request))
        self.assertTrue(self.order_admin.has_change_permission(staff_request))
        self.assertFalse(self.profile_admin.has_view_permission(staff_request))

    def test_staff_has_limited_order_actions(self):
        staff_request = self._request_for(self.staff_user)
        actions = self.order_admin.get_actions(staff_request)
        self.assertNotIn("mark_paid", actions)
        self.assertIn("mark_confirmed", actions)
        self.assertIn("mark_shipping", actions)
        self.assertNotIn("mark_completed", actions)
        self.assertNotIn("mark_cancelled", actions)

    def test_manager_sees_all_order_actions_and_roles(self):
        manager_request = self._request_for(self.manager_user)
        actions = self.order_admin.get_actions(manager_request)
        self.assertIn("mark_paid", actions)
        self.assertIn("mark_confirmed", actions)
        self.assertIn("mark_shipping", actions)
        self.assertIn("mark_completed", actions)
        self.assertIn("mark_cancelled", actions)
        self.assertTrue(self.profile_admin.has_view_permission(manager_request))


class ShopAdminDashboardTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="pass12345",
        )
        self.category = Category.objects.create(name="Cardio", description="Dụng cụ cardio")
        self.product = Product.objects.create(
            category=self.category,
            name="Treadmill",
            price=Decimal("12500000.00"),
            description="Máy chạy bộ",
            stock=3,
        )
        self.order = Order.objects.create(
            user=self.admin_user,
            full_name="Admin",
            phone="0901234567",
            email="admin@example.com",
            province="TP. Hồ Chí Minh",
            district="Quận 1",
            ward="Bến Nghé",
            street_address="123 Lê Lợi",
            shipping_address="123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            subtotal=Decimal("12500000.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("12500000.00"),
            payment_method=Order.METHOD_VNPAY,
            payment_status=Order.PAYMENT_PAID,
            order_status=Order.STATUS_COMPLETED,
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=1,
            line_total=self.product.price,
        )

    def test_admin_dashboard_exposes_sales_metrics(self):
        request = self.factory.get("/admin/")
        request.user = self.admin_user

        response = admin_site.index(request)
        response.render()

        self.assertEqual(response.status_code, 200)
        metrics = {metric["label"]: metric for metric in response.context_data["dashboard_metrics"]}
        self.assertEqual(metrics["Tổng đơn hàng"]["value"], 1)
        self.assertEqual(metrics["Doanh thu đã ghi nhận"]["value"], Decimal("12500000.00"))
        self.assertEqual(len(response.context_data["recent_orders"]), 1)
        self.assertEqual(response.context_data["top_products"][0].sold_quantity, 1)
