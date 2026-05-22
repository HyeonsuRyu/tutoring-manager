from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="student",
            name="hourly_rate",
            field=models.DecimalField(decimal_places=0, default=10000, max_digits=12),
        ),
    ]
