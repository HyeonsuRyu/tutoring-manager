from django.conf import settings
from django.db import models


class Subject(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subjects"
    )
    name = models.CharField(max_length=128)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="uniq_subject_owner_name"),
        ]

    def __str__(self) -> str:
        return self.name


class Student(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="students"
    )
    name = models.CharField(max_length=128)
    birth_year = models.PositiveIntegerField()
    grade = models.CharField(max_length=32)
    country = models.CharField(max_length=8, default="KR")
    city = models.CharField(max_length=128, blank=True)
    timezone = models.CharField(max_length=64, default="Asia/Seoul")
    student_contact = models.CharField(max_length=64, blank=True)
    parent_name = models.CharField(max_length=128, blank=True)
    parent_contact = models.CharField(max_length=64, blank=True)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=0, default=10000)
    lesson_duration_minutes = models.PositiveSmallIntegerField(default=60)
    lessons_completed = models.PositiveIntegerField(default=0)
    subjects = models.ManyToManyField(Subject, blank=True, related_name="students")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def age(self) -> int:
        from datetime import date

        return date.today().year - self.birth_year

    @property
    def next_lesson_number(self) -> int:
        return self.lessons_completed + 1

    def __str__(self) -> str:
        return self.name


class ScheduleSlot(models.Model):
    class DayOfWeek(models.IntegerChoices):
        SUNDAY = 0, "일"
        MONDAY = 1, "월"
        TUESDAY = 2, "화"
        WEDNESDAY = 3, "수"
        THURSDAY = 4, "목"
        FRIDAY = 5, "금"
        SATURDAY = 6, "토"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="schedule_slots")
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.student.name} {self.get_day_of_week_display()} {self.start_time}"


class StudentDetail(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="detail")
    long_memo = models.TextField(blank=True)


class GoalHistoryEntry(models.Model):
    class EntryType(models.TextChoices):
        GOAL = "goal", "목표"
        PROGRESS = "progress", "진도"
        CONSULTATION = "consultation", "상담"
        OTHER = "other", "기타"

    detail = models.ForeignKey(StudentDetail, on_delete=models.CASCADE, related_name="history_entries")
    entry_date = models.DateField()
    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        ordering = ["-entry_date", "-pk"]
