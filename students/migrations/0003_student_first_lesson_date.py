from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0002_alter_student_hourly_rate_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="first_lesson_date",
            field=models.DateField(
                blank=True,
                help_text="이 날짜 이전에는 달력에 정규 수업 제안·표시가 나오지 않습니다.",
                null=True,
            ),
        ),
    ]
