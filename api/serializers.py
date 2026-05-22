from rest_framework import serializers

from calendar_app.models import Lesson
from students.models import GoalHistoryEntry, ScheduleSlot, Student, StudentDetail, Subject


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


class ScheduleSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleSlot
        fields = ["id", "day_of_week", "start_time", "end_time", "note"]


class StudentListSerializer(serializers.ModelSerializer):
    next_lesson_number = serializers.IntegerField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "name",
            "grade",
            "birth_year",
            "age",
            "lessons_completed",
            "next_lesson_number",
            "lesson_duration_minutes",
            "first_lesson_date",
        ]


class StudentSerializer(serializers.ModelSerializer):
    next_lesson_number = serializers.IntegerField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    subject_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Subject.objects.all(), source="subjects", required=False
    )
    schedule_slots = ScheduleSlotSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "name",
            "birth_year",
            "age",
            "grade",
            "timezone",
            "student_contact",
            "parent_name",
            "parent_contact",
            "subject_ids",
            "hourly_rate",
            "first_lesson_date",
            "lesson_duration_minutes",
            "lessons_completed",
            "next_lesson_number",
            "schedule_slots",
        ]
        read_only_fields = ["id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["subject_ids"].queryset = Subject.objects.filter(owner=request.user)

    def create(self, validated_data):
        subjects = validated_data.pop("subjects", [])
        validated_data["owner"] = self.context["request"].user
        student = super().create(validated_data)
        if subjects:
            student.subjects.set(subjects)
        return student


class GoalHistoryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalHistoryEntry
        fields = ["id", "entry_date", "entry_type", "title", "body"]


class StudentDetailSerializer(serializers.ModelSerializer):
    goal_history = GoalHistoryEntrySerializer(many=True, read_only=True, source="history_entries")

    class Meta:
        model = StudentDetail
        fields = ["long_memo", "goal_history"]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "student",
            "schedule_slot",
            "date",
            "start_datetime",
            "end_datetime",
            "lesson_number",
            "status",
            "lesson_content",
            "lesson_notes",
            "lesson_kind",
            "course_name",
            "cancelled_by",
            "cancel_reason",
            "makeup_status",
            "makeup_date",
        ]
        read_only_fields = ["id", "lesson_number"]


class ApproveProposalSerializer(serializers.Serializer):
    schedule_slot_id = serializers.IntegerField()
    date = serializers.DateField()


class DismissProposalSerializer(serializers.Serializer):
    schedule_slot_id = serializers.IntegerField()
    date = serializers.DateField()


class CancelLessonSerializer(serializers.Serializer):
    cancelled_by = serializers.ChoiceField(choices=Lesson.CancelledBy.choices)
    cancel_reason = serializers.CharField(required=False, allow_blank=True, default="")
    makeup_status = serializers.ChoiceField(choices=Lesson.MakeupStatus.choices, default="undecided")
    makeup_date = serializers.DateField(required=False, allow_null=True, default=None)
