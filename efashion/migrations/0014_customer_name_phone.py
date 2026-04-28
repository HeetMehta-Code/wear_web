from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('efashion', '0013_contactmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='phone',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
