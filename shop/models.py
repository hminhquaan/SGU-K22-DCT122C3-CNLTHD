import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    description = models.TextField()
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.stock > 0

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    @property
    def subtotal(self):
        total = Decimal("0.00")
        for item in self.items.select_related("product"):
            total += item.line_total
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def line_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Order(models.Model):
    PAYMENT_PENDING = "PENDING"
    PAYMENT_PAID = "PAID"
    PAYMENT_COD = PAYMENT_PENDING

    PAYMENT_FAILED = "FAILED"
    PAYMENT_CANCELLED = "CANCELLED"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Chờ thanh toán"),
        (PAYMENT_PAID, "Đã thanh toán"),
        (PAYMENT_FAILED, "Thanh toán thất bại"),
        (PAYMENT_CANCELLED, "Đã hủy thanh toán"),
    ]

    METHOD_COD = "COD"
    METHOD_BANK_TRANSFER = "BANK_TRANSFER"
    METHOD_MOMO = "MOMO"
    METHOD_ZALOPAY = "ZALOPAY"
    METHOD_VNPAY = "VNPAY"

    PAYMENT_METHOD_CHOICES = [
        (METHOD_COD, "Thanh toán khi nhận hàng"),
        (METHOD_BANK_TRANSFER, "Chuyển khoản ngân hàng"),
        (METHOD_MOMO, "Ví MoMo"),
        (METHOD_ZALOPAY, "Ví ZaloPay"),
        (METHOD_VNPAY, "VNPay"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPING = "SHIPPING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    ORDER_STATUS_CHOICES = [
        (STATUS_PENDING, "Chờ xác nhận"),
        (STATUS_CONFIRMED, "Đã xác nhận"),
        (STATUS_SHIPPING, "Đang giao"),
        (STATUS_COMPLETED, "Hoàn tất"),
        (STATUS_CANCELLED, "Đã hủy"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    tracking_code = models.CharField(max_length=32, unique=True, blank=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    province = models.CharField(max_length=100, blank=True, default="")
    district = models.CharField(max_length=100, blank=True, default="")
    ward = models.CharField(max_length=100, blank=True, default="")
    street_address = models.CharField(max_length=255, blank=True, default="")
    delivery_place_name = models.CharField(max_length=255, blank=True, default="")
    delivery_place_id = models.CharField(max_length=255, blank=True, default="")
    delivery_map_provider = models.CharField(max_length=32, blank=True, default="")
    delivery_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    shipping_address = models.TextField()
    note = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=METHOD_COD)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=STATUS_PENDING)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipping_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    customer_payment_notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = f"ZF{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"

    def restore_inventory_and_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        for item in self.items.select_related("product"):
            if not item.product_id:
                continue
            Product.objects.filter(id=item.product_id).update(stock=models.F("stock") + item.quantity)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=item.product, defaults={"quantity": item.quantity})
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save(update_fields=["quantity", "updated_at"])

    @property
    def display_tracking_code(self):
        return self.tracking_code or f"ZF{self.pk:06d}"

    @property
    def formatted_shipping_address(self):
        parts = [self.street_address, self.ward, self.district, self.province]
        merged = ", ".join(part for part in parts if part)
        return merged or self.shipping_address

    @property
    def delivery_location_summary(self):
        if self.delivery_place_name:
            return self.delivery_place_name
        if self.delivery_latitude is not None and self.delivery_longitude is not None:
            return f"{self.delivery_latitude}, {self.delivery_longitude}"
        return self.formatted_shipping_address

    @property
    def payment_method_label(self):
        return self.get_payment_method_display()

    @property
    def payment_status_label(self):
        return self.get_payment_status_display()

    @property
    def is_online_payment(self):
        return self.payment_method != self.METHOD_COD

    @property
    def is_purchase_successful(self):
        return self.payment_status == self.PAYMENT_PAID and self.order_status != self.STATUS_CANCELLED

    @property
    def payment_details(self):
        details = {
            self.METHOD_COD: {
                "title": "Thanh toán khi nhận hàng",
                "description": "Bạn chỉ cần nhận hàng và thanh toán cho nhân viên giao hàng.",
                "action_label": "Tiếp tục theo dõi đơn",
            },
            self.METHOD_BANK_TRANSFER: {
                "title": "Chuyển khoản ngân hàng",
                "description": "Chuyển khoản theo nội dung bên dưới để hệ thống xác nhận đơn nhanh hơn.",
                "account_name": "ZENITH FITNESS",
                "account_number": "0123456789",
                "bank_name": "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)",
                "transfer_content": self.display_tracking_code,
                "action_label": "Tôi đã chuyển khoản",
            },
            self.METHOD_MOMO: {
                "title": "Thanh toán qua MoMo",
                "description": "Quét mã QR hoặc mở ví MoMo theo hướng dẫn để hoàn tất thanh toán.",
                "merchant": "ZENITH FITNESS",
                "transfer_content": self.display_tracking_code,
                "action_label": "Tôi đã thanh toán MoMo",
            },
            self.METHOD_ZALOPAY: {
                "title": "Thanh toán qua ZaloPay",
                "description": "Hoàn tất thanh toán trong ví ZaloPay và giữ mã giao dịch để đối soát.",
                "merchant": "ZENITH FITNESS",
                "transfer_content": self.display_tracking_code,
                "action_label": "Tôi đã thanh toán ZaloPay",
            },
            self.METHOD_VNPAY: {
                "title": "Thanh toán qua VNPay",
                "description": "Thanh toán online qua VNPay bằng mã đơn hiện tại.",
                "merchant": "ZENITH FITNESS",
                "transfer_content": self.display_tracking_code,
                "action_label": "Tôi đã thanh toán VNPay",
            },
        }
        return details.get(self.payment_method, details[self.METHOD_COD])

    @property
    def tracking_timeline(self):
        return [
            {
                "key": self.STATUS_PENDING,
                "label": "Đã tiếp nhận đơn hàng",
                "description": "Hệ thống đã ghi nhận yêu cầu đặt hàng của bạn.",
                "timestamp": self.created_at,
                "done": True,
                "active": self.order_status == self.STATUS_PENDING,
            },
            {
                "key": self.STATUS_CONFIRMED,
                "label": "Đã xác nhận",
                "description": "Đơn hàng đang được xác minh và chuẩn bị hàng.",
                "timestamp": self.confirmed_at,
                "done": self.order_status in {self.STATUS_CONFIRMED, self.STATUS_SHIPPING, self.STATUS_COMPLETED},
                "active": self.order_status == self.STATUS_CONFIRMED,
            },
            {
                "key": self.STATUS_SHIPPING,
                "label": "Đang giao hàng",
                "description": "Đơn hàng đã rời kho và đang trên đường đến bạn.",
                "timestamp": self.shipping_at,
                "done": self.order_status in {self.STATUS_SHIPPING, self.STATUS_COMPLETED},
                "active": self.order_status == self.STATUS_SHIPPING,
            },
            {
                "key": self.STATUS_COMPLETED,
                "label": "Hoàn tất",
                "description": "Đơn hàng đã giao thành công và kết thúc quy trình.",
                "timestamp": self.completed_at,
                "done": self.order_status == self.STATUS_COMPLETED,
                "active": self.order_status == self.STATUS_COMPLETED,
            },
            {
                "key": self.STATUS_CANCELLED,
                "label": "Đã hủy",
                "description": "Đơn hàng đã bị hủy theo yêu cầu hoặc do không thể xử lý tiếp.",
                "timestamp": self.cancelled_at,
                "done": self.order_status == self.STATUS_CANCELLED,
                "active": self.order_status == self.STATUS_CANCELLED,
            },
        ]

    @property
    def status_timestamp(self):
        return {
            self.STATUS_PENDING: self.created_at,
            self.STATUS_CONFIRMED: self.confirmed_at,
            self.STATUS_SHIPPING: self.shipping_at,
            self.STATUS_COMPLETED: self.completed_at,
            self.STATUS_CANCELLED: self.cancelled_at,
        }.get(self.order_status)

    def mark_status(self, status):
        now = timezone.now()
        if status == self.STATUS_CANCELLED and self.order_status != self.STATUS_CANCELLED:
            self.restore_inventory_and_cart()

        update_fields = [
            "order_status",
            "confirmed_at",
            "shipping_at",
            "completed_at",
            "cancelled_at",
            "customer_payment_notified_at",
            "updated_at",
        ]

        self.order_status = status
        if status == self.STATUS_CONFIRMED:
            self.confirmed_at = self.confirmed_at or now
        elif status == self.STATUS_SHIPPING:
            self.confirmed_at = self.confirmed_at or now
            self.shipping_at = self.shipping_at or now
        elif status == self.STATUS_COMPLETED:
            self.confirmed_at = self.confirmed_at or now
            self.shipping_at = self.shipping_at or now
            self.completed_at = now
            if self.payment_method == self.METHOD_COD and self.payment_status != self.PAYMENT_PAID:
                self.payment_status = self.PAYMENT_PAID
                update_fields.append("payment_status")
        elif status == self.STATUS_CANCELLED:
            if self.is_online_payment and self.payment_status == self.PAYMENT_PENDING:
                self.payment_status = self.PAYMENT_CANCELLED
                update_fields.append("payment_status")
            self.cancelled_at = now
        self.save(update_fields=update_fields)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class UserProfile(models.Model):
    ROLE_CUSTOMER = "CUSTOMER"
    ROLE_STAFF = "STAFF"
    ROLE_OPERATOR = "OPERATOR"
    ROLE_MANAGER = "MANAGER"

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, "Khách hàng"),
        (ROLE_STAFF, "Nhân viên"),
        (ROLE_OPERATOR, "Nhân viên vận hành"),
        (ROLE_MANAGER, "Quản lý"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER

    @property
    def is_staff_role(self):
        return self.role in {self.ROLE_STAFF, self.ROLE_OPERATOR, self.ROLE_MANAGER}

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER
