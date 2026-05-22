from django import forms
from django.forms import inlineformset_factory

from students.models import GoalHistoryEntry, ScheduleSlot, Student, StudentDetail, Subject

GRADE_CHOICES = [
    ("", "선택 또는 직접 입력"),
    ("초1", "초1"),
    ("초2", "초2"),
    ("초3", "초3"),
    ("초4", "초4"),
    ("초5", "초5"),
    ("초6", "초6"),
    ("중1", "중1"),
    ("중2", "중2"),
    ("중3", "중3"),
    ("고1", "고1"),
    ("고2", "고2"),
    ("고3", "고3"),
    ("N수", "N수"),
    ("성인", "성인"),
    ("기타", "기타"),
]


class StudentForm(forms.ModelForm):
    grade = forms.CharField(
        label="학년",
        widget=forms.TextInput(attrs={"list": "grade-suggestions"}),
    )

    class Meta:
        model = Student
        fields = [
            "name",
            "birth_year",
            "grade",
            "country",
            "city",
            "timezone",
            "student_contact",
            "parent_name",
            "parent_contact",
            "hourly_rate",
            "lesson_duration_minutes",
            "lessons_completed",
            "subjects",
        ]
        labels = {
            "name": "이름",
            "birth_year": "출생 연도",
            "grade": "학년",
            "country": "국가",
            "city": "도시",
            "timezone": "시간대",
            "student_contact": "학생 연락처",
            "parent_name": "보호자 이름",
            "parent_contact": "보호자 연락처",
            "hourly_rate": "시간당 수업료",
            "lesson_duration_minutes": "수업 시간(분)",
            "lessons_completed": "완료 회차",
            "subjects": "과목",
        }
        widgets = {
            "subjects": forms.CheckboxSelectMultiple,
            "timezone": forms.TextInput(attrs={"list": "timezone-suggestions"}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner:
            self.fields["subjects"].queryset = Subject.objects.filter(owner=owner)


class ScheduleSlotForm(forms.ModelForm):
    class Meta:
        model = ScheduleSlot
        fields = ["day_of_week", "start_time", "end_time", "note"]
        labels = {
            "day_of_week": "요일",
            "start_time": "시작 시간",
            "end_time": "종료 시간",
            "note": "메모",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "DELETE" in self.fields:
            self.fields["DELETE"].label = "삭제"


ScheduleSlotFormSet = inlineformset_factory(
    Student,
    ScheduleSlot,
    form=ScheduleSlotForm,
    fields=["day_of_week", "start_time", "end_time", "note"],
    extra=1,
    can_delete=True,
)


class StudentDetailForm(forms.ModelForm):
    class Meta:
        model = StudentDetail
        fields = ["long_memo"]
        widgets = {"long_memo": forms.Textarea(attrs={"rows": 6})}


class GoalHistoryEntryForm(forms.ModelForm):
    class Meta:
        model = GoalHistoryEntry
        fields = ["entry_date", "entry_type", "title", "body"]


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name"]
