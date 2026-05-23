from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar_app", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="lesson",
            index=models.Index(fields=["student", "date"], name="cal_lesson_student_date_idx"),
        ),
    ]
