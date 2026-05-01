from django.db import migrations


def populate_tracking_codes(apps, schema_editor):
    Order = apps.get_model("shop", "Order")
    for order in Order.objects.filter(tracking_code=""):
        order.tracking_code = f"ZF{order.pk:06d}"
        order.save(update_fields=["tracking_code"])


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0002_order_cancelled_at_order_completed_at_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_tracking_codes, migrations.RunPython.noop),
    ]
