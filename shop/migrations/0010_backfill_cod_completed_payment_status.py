from django.db import migrations


def backfill_cod_completed_orders(apps, schema_editor):
    Order = apps.get_model("shop", "Order")
    Order.objects.filter(payment_method="COD", order_status="COMPLETED", payment_status="PENDING").update(payment_status="PAID")


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0009_remove_order_paid_at"),
    ]

    operations = [
        migrations.RunPython(backfill_cod_completed_orders, noop_reverse),
    ]