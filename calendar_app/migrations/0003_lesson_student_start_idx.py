from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar_app", "0002_lesson_student_date_idx"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="lesson",
            index=models.Index(
                fields=["student", "start_datetime"],
                name="cal_lesson_student_start_idx",
            ),
        ),
    ]
