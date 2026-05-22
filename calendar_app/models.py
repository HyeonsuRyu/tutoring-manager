from django.conf import settings
from django.db import models


class Lesson(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "예정"
        COMPLETED = "completed", "완료"
        CANCELLED = "cancelled", "취소"

    class LessonKind(models.TextChoices):
        REGULAR = "regular", "정규"
        TEST = "test", "테스트"

    class CancelledBy(models.TextChoices):
        STUDENT = "student", "학생"
        TEACHER = "teacher", "교사"

    class MakeupStatus(models.TextChoices):
        UNDECIDED = "undecided", "미정"
        NO_MAKEUP = "no_makeup", "없음"
        SCHEDULED = "scheduled", "예정"

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="lessons")
    schedule_slot = models.ForeignKey(
        "students.ScheduleSlot",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons",
    )
    date = models.DateField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    lesson_number = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_counted = models.BooleanField(default=False)
    lesson_content = models.TextField(blank=True)
    lesson_notes = models.TextField(blank=True)
    lesson_kind = models.CharField(
        max_length=16, choices=LessonKind.choices, default=LessonKind.REGULAR
    )
    course_name = models.CharField(max_length=255, blank=True)
    cancelled_by = models.CharField(max_length=16, choices=CancelledBy.choices, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    makeup_status = models.CharField(
        max_length=16, choices=MakeupStatus.choices, default=MakeupStatus.UNDECIDED, blank=True
    )
    makeup_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self) -> str:
        return f"{self.student.name} #{self.lesson_number} {self.date}"


class LessonProposalDismissal(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    schedule_slot = models.ForeignKey("students.ScheduleSlot", on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["schedule_slot", "date"],
                name="uniq_dismissal_slot_date",
            ),
        ]
