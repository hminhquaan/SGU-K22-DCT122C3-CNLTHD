from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncMonth
from django.utils import timezone

from unfold.sites import UnfoldAdminSite

from .models import Order, Product


class ShopAdminSite(UnfoldAdminSite):
    site_header = "ZENITH FITNESS"
    site_title = "ZENITH FITNESS Admin"
    index_title = "Bảng điều khiển bán hàng"
    site_url = "/"

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
            revenue_labels.append(day.strftime("%d/%m"))
            revenue_values.append(int(revenue_by_day.get(day, Decimal("0"))))

        peak_index = max(range(len(revenue_values)), key=lambda index: revenue_values[index]) if revenue_values else None
        peak_label = revenue_labels[peak_index] if peak_index is not None and revenue_values[peak_index] > 0 else "Chưa có dữ liệu"
        peak_value = revenue_values[peak_index] if peak_index is not None else 0
        revenue_chart_has_data = any(value > 0 for value in revenue_values)

        def move_months(date_value, months):
            month_index = date_value.month - 1 + months
            year = date_value.year + month_index // 12
            month = month_index % 12 + 1
            return date_value.replace(year=year, month=month, day=1)

        month_start = move_months(today.replace(day=1), -11)
        monthly_series_qs = (
            completed_orders.filter(payment_status=Order.PAYMENT_PAID, created_at__date__gte=month_start)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Coalesce(Sum("total_amount"), Decimal("0.00")))
            .order_by("month")
        )
        revenue_by_month = {row["month"]: row["total"] for row in monthly_series_qs}
        monthly_labels = []
        monthly_values = []
        month_cursor = month_start
        for _ in range(12):
            monthly_labels.append(month_cursor.strftime("%m/%Y"))
            monthly_values.append(int(revenue_by_month.get(month_cursor, Decimal("0"))))
            month_cursor = move_months(month_cursor, 1)

        revenue_chart_mode = "daily" if revenue_chart_has_data else "monthly"
        revenue_chart_title = "Doanh thu 30 ngày gần đây" if revenue_chart_mode == "daily" else "Doanh thu theo tháng"
        revenue_chart_labels = revenue_labels if revenue_chart_mode == "daily" else monthly_labels
        revenue_chart_values = revenue_values if revenue_chart_mode == "daily" else monthly_values
        revenue_chart_has_any_data = any(value > 0 for value in revenue_chart_values)

        total_orders = Order.objects.count()
        recent_orders_count = Order.objects.filter(created_at__gte=recent_window).count()
        paid_orders_count = completed_orders.filter(payment_status=Order.PAYMENT_PAID).count()
        pending_orders = Order.objects.filter(order_status=Order.STATUS_PENDING).count()
        confirmed_orders = Order.objects.filter(order_status=Order.STATUS_CONFIRMED).count()
        shipping_orders = Order.objects.filter(order_status=Order.STATUS_SHIPPING).count()
        completed_count = Order.objects.filter(order_status=Order.STATUS_COMPLETED).count()
        cancelled_orders = Order.objects.filter(order_status=Order.STATUS_CANCELLED).count()
        average_order_value = revenue_total / paid_orders_count if paid_orders_count else Decimal("0.00")

        active_products = Product.objects.filter(is_active=True).count()
        low_stock_queryset = Product.objects.filter(is_active=True, stock__lte=10).order_by("stock", "name")
        low_stock_products = low_stock_queryset[:6]
        low_stock_count = low_stock_queryset.count()
        top_products = (
            Product.objects.filter(is_active=True)
            .annotate(
                sold_quantity=Coalesce(Sum("orderitem__quantity", filter=Q(orderitem__order__payment_status=Order.PAYMENT_PAID)), 0),
                sold_revenue=Coalesce(Sum("orderitem__line_total", filter=Q(orderitem__order__payment_status=Order.PAYMENT_PAID)), Decimal("0.00")),
            )
            .order_by("-sold_quantity", "-created_at", "name")[:5]
        )
        recent_orders = Order.objects.select_related("user").order_by("-created_at")[:8]

        return {
            "dashboard_period_label": "30 ngày gần đây",
            "dashboard_title": "Tổng quan cửa hàng",
            "dashboard_summary": [
                {"label": "Doanh thu đã thanh toán", "value": format_vnd(revenue_total), "note": f"{format_vnd(revenue_recent)} trong 30 ngày gần đây" if revenue_recent else "Chưa có doanh thu gần đây"},
                {"label": "Đơn đã thanh toán", "value": f"{paid_orders_count}", "note": f"Trung bình {format_vnd(average_order_value)} mỗi đơn" if paid_orders_count else "Chưa có đơn thanh toán"},
                {"label": "Đơn đang chờ", "value": f"{pending_orders}", "note": "Cần ưu tiên xử lý sớm"},
                {"label": "Sản phẩm cần nhập", "value": f"{low_stock_count}", "note": "Còn ít hàng hoặc sắp hết hàng"},
            ],
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
                    "note": f"{low_stock_count} sản phẩm cần nhập thêm",
                },
            ],
            "revenue_total_display": format_vnd(revenue_total),
            "average_order_value_display": format_vnd(average_order_value),
            "total_orders_count": total_orders,
            "revenue_chart_title": revenue_chart_title,
            "revenue_chart_mode": revenue_chart_mode,
            "revenue_chart_labels": revenue_chart_labels,
            "revenue_chart_values": revenue_chart_values,
            "revenue_chart_has_any_data": revenue_chart_has_any_data,
            "revenue_chart_has_data": revenue_chart_has_data,
            "revenue_peak_label": peak_label,
            "revenue_peak_value": peak_value,
            "status_chart_labels": ["Chờ xác nhận", "Đã xác nhận", "Đang giao", "Hoàn tất", "Đã hủy"],
            "status_chart_values": [pending_orders, confirmed_orders, shipping_orders, completed_count, cancelled_orders],
            "recent_orders": recent_orders,
            "low_stock_products": low_stock_products,
            "top_products": top_products,
            "low_stock_count": low_stock_count,
            "paid_orders_count": paid_orders_count,
            "average_order_value": average_order_value,
        }


def dashboard_callback(request, context):
    context.update(admin_site.get_dashboard_context())
    return context


admin_site = ShopAdminSite(name="admin")