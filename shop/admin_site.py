from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncDate
from django.utils import timezone

from unfold.sites import UnfoldAdminSite

from .models import Order, Product


class ShopAdminSite(UnfoldAdminSite):
    site_header = "ZENITH FITNESS"
    site_title = "ZENITH FITNESS Admin"
    index_title = "Dashboard bán hàng"
    site_url = "/"

    def index(self, request, extra_context=None):
        context = extra_context or {}
        context.update(self.get_dashboard_context())
        return super().index(request, extra_context=context)

    def get_dashboard_context(self):
        def format_vnd(amount: Decimal) -> str:
            rounded = int((amount or Decimal("0")).quantize(Decimal("1")))
            return f"{rounded:,}".replace(",", ".") + " ₫"

        recent_window = timezone.now() - timedelta(days=30)
        completed_orders = Order.objects.exclude(order_status=Order.STATUS_CANCELLED)
        revenue_total = completed_orders.filter(payment_status=Order.PAYMENT_PAID).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        revenue_recent = completed_orders.filter(payment_status=Order.PAYMENT_PAID, created_at__gte=recent_window).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

        # Revenue chart (daily) for the last 30 days (paid orders, not cancelled)
        today = timezone.localdate()
        start_day = today - timedelta(days=29)
        revenue_series_qs = (
            completed_orders.filter(payment_status=Order.PAYMENT_PAID, created_at__date__gte=start_day)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Coalesce(Sum("total_amount"), Decimal("0.00")))
            .order_by("day")
        )
        revenue_by_day = {row["day"]: row["total"] for row in revenue_series_qs}
        revenue_labels = []
        revenue_values = []
        for offset in range(30):
            day = start_day + timedelta(days=offset)
            revenue_labels.append(day.isoformat())
            revenue_values.append(int(revenue_by_day.get(day, Decimal("0"))))

        total_orders = Order.objects.count()
        recent_orders_count = Order.objects.filter(created_at__gte=recent_window).count()
        pending_orders = Order.objects.filter(order_status=Order.STATUS_PENDING).count()
        confirmed_orders = Order.objects.filter(order_status=Order.STATUS_CONFIRMED).count()
        shipping_orders = Order.objects.filter(order_status=Order.STATUS_SHIPPING).count()
        completed_count = Order.objects.filter(order_status=Order.STATUS_COMPLETED).count()
        cancelled_orders = Order.objects.filter(order_status=Order.STATUS_CANCELLED).count()

        active_products = Product.objects.filter(is_active=True).count()
        low_stock_products = Product.objects.filter(is_active=True, stock__lte=10).order_by("stock", "name")[:5]
        top_products = (
            Product.objects.filter(is_active=True)
            .annotate(sold_quantity=Coalesce(Sum("orderitem__quantity", filter=Q(orderitem__order__payment_status=Order.PAYMENT_PAID)), 0))
            .order_by("-sold_quantity", "-created_at", "name")[:5]
        )
        recent_orders = Order.objects.select_related("user").order_by("-created_at")[:6]

        return {
            "dashboard_period_label": "30 ngày gần đây",
            "dashboard_metrics": [
                {
                    "label": "Doanh thu đã ghi nhận",
                    "value": revenue_total,
                    "value_display": format_vnd(revenue_total),
                    "kind": "currency",
                    "note": f"{format_vnd(revenue_recent)} trong 30 ngày gần đây" if revenue_recent else "Chưa có doanh thu gần đây",
                },
                {
                    "label": "Tổng đơn hàng",
                    "value": total_orders,
                    "kind": "count",
                    "note": f"{recent_orders_count} đơn trong 30 ngày gần đây",
                },
                {
                    "label": "Đơn chờ xác nhận",
                    "value": pending_orders,
                    "kind": "count",
                    "note": "Nên xử lý sớm để tránh chậm giao",
                },
                {
                    "label": "Sản phẩm hoạt động",
                    "value": active_products,
                    "kind": "count",
                    "note": f"{Product.objects.filter(is_active=True, stock__lte=10).count()} sản phẩm sắp hết hàng",
                },
            ],
            "order_status_breakdown": [
                {"label": "Chờ xác nhận", "count": pending_orders},
                {"label": "Đã xác nhận", "count": confirmed_orders},
                {"label": "Đang giao", "count": shipping_orders},
                {"label": "Hoàn tất", "count": completed_count},
                {"label": "Đã hủy", "count": cancelled_orders},
            ],
            "revenue_chart_labels": revenue_labels,
            "revenue_chart_values": revenue_values,
            "status_chart_labels": ["Chờ xác nhận", "Đã xác nhận", "Đang giao", "Hoàn tất", "Đã hủy"],
            "status_chart_values": [pending_orders, confirmed_orders, shipping_orders, completed_count, cancelled_orders],
            "recent_orders": recent_orders,
            "low_stock_products": low_stock_products,
            "top_products": top_products,
        }


admin_site = ShopAdminSite(name="admin")