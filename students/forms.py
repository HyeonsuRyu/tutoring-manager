from datetime import time

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from core.timezone_suggest import timezone_choices_ko
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

TIME_INPUT_CLASS = "slot-time-input"
DEFAULT_SLOT_TIME = time(12, 0)
DEFAULT_HOURLY_RATE = 10000


class StudentForm(forms.ModelForm):
    grade = forms.CharField(
        label="학년",
        widget=forms.TextInput(
            attrs={
                "list": "grade-suggestions",
                "autocomplete": "off",
                "class": "grade-sync-field",
                "data-grade-sync": "grade",
            }
        ),
    )
    hourly_rate = forms.CharField(
        label="시간당 수업료",
        widget=forms.TextInput(
            attrs={
                "class": "hourly-rate-input",
                "inputmode": "numeric",
                "autocomplete": "off",
                "placeholder": "10,000",
            }
        ),
    )

    class Meta:
        model = Student
        fields = [
            "name",
            "birth_year",
            "grade",
            "timezone",
            "student_contact",
            "parent_name",
            "parent_contact",
            "lesson_duration_minutes",
            "lessons_completed",
            "subjects",
        ]
        labels = {
            "name": "이름",
            "birth_year": "출생 연도",
            "grade": "학년",
            "timezone": "시간대",
            "student_contact": "학생 연락처",
            "parent_name": "학부모 성함",
            "parent_contact": "학부모 연락처",
            "lesson_duration_minutes": "1회 수업(분)",
            "lessons_completed": "완료 회차",
            "subjects": "과목",
        }
        widgets = {
            "subjects": forms.CheckboxSelectMultiple,
            "birth_year": forms.NumberInput(
                attrs={
                    "class": "grade-sync-field",
                    "data-grade-sync": "birth_year",
                    "list": "birth-year-suggestions",
                    "autocomplete": "off",
                    "min": "1990",
                    "max": "2035",
                }
            ),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner:
            self.fields["subjects"].queryset = Subject.objects.filter(owner=owner)
        current_tz = getattr(self.instance, "timezone", None) or "Asia/Seoul"
        self.fields["timezone"] = forms.ChoiceField(
            label="시간대",
            choices=timezone_choices_ko(current_tz),
            initial=current_tz,
            widget=forms.Select(attrs={"class": "timezone-select"}),
        )
        if self.instance.pk and self.instance.hourly_rate is not None:
            self.fields["hourly_rate"].initial = f"{int(self.instance.hourly_rate):,}"
        else:
            self.fields["hourly_rate"].initial = f"{DEFAULT_HOURLY_RATE:,}"

    def clean_hourly_rate(self):
        raw = str(self.cleaned_data.get("hourly_rate", "")).replace(",", "").replace("원", "").strip()
        if not raw:
            raise forms.ValidationError("시간당 수업료를 입력하세요.")
        if not raw.isdigit():
            raise forms.ValidationError("숫자만 입력할 수 있습니다.")
        return int(raw)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.hourly_rate = self.cleaned_data["hourly_rate"]
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ScheduleSlotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "DELETE" in self.fields:
            self.fields["DELETE"].widget = forms.HiddenInput()
        if not self.instance.pk:
            for field_name in ("start_time", "end_time"):
                self.initial.setdefault(field_name, DEFAULT_SLOT_TIME)

    start_time = forms.TimeField(
        label="시작",
        widget=forms.TimeInput(attrs={"type": "time", "class": TIME_INPUT_CLASS}),
    )
    end_time = forms.TimeField(
        label="종료",
        widget=forms.TimeInput(attrs={"type": "time", "class": TIME_INPUT_CLASS}),
    )

    class Meta:
        model = ScheduleSlot
        fields = ["day_of_week", "start_time", "end_time"]
        labels = {
            "day_of_week": "요일",
        }


class ScheduleSlotFormSetBase(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = True


ScheduleSlotFormSet = inlineformset_factory(
    Student,
    ScheduleSlot,
    form=ScheduleSlotForm,
    formset=ScheduleSlotFormSetBase,
    fields=["day_of_week", "start_time", "end_time"],
    extra=1,
    min_num=0,
    max_num=20,
    can_delete=True,
)


class StudentDetailForm(forms.ModelForm):
    class Meta:
        model = StudentDetail
        fields = ["long_memo"]
        labels = {"long_memo": "메모"}
        widgets = {"long_memo": forms.Textarea(attrs={"rows": 3})}


class GoalHistoryEntryForm(forms.ModelForm):
    class Meta:
        model = GoalHistoryEntry
        fields = ["entry_date", "entry_type", "title", "body"]


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name"]
