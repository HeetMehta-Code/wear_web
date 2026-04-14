from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('efashion', '0011_order_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_address',
            field=models.TextField(blank=True, null=True),
        ),
    ]
