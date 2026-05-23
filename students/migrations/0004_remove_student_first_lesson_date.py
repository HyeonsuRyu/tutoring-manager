from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0003_student_first_lesson_date"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="student",
            name="first_lesson_date",
        ),
    ]
