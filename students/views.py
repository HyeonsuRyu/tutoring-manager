from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.contact_mask import mask_contact
from core.timezone_suggest import list_common_timezones
from students.forms import GoalHistoryEntryForm, ScheduleSlotFormSet, StudentDetailForm, StudentForm, SubjectForm
from students.import_prefill import build_student_prefill
from students.models import GoalHistoryEntry, Student, StudentDetail, Subject
from students.views_progress_import import SESSION_KEY as PROGRESS_IMPORT_SESSION_KEY


class OwnerQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class StudentListView(OwnerQuerysetMixin, ListView):
    model = Student
    template_name = "students/list.html"
    context_object_name = "students"

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("subjects", "schedule_slots")
        sort = self.request.GET.get("sort", "name")
        if sort == "grade":
            return qs.order_by("grade", "name")
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for s in ctx["students"]:
            s.masked_student_contact = mask_contact(s.student_contact)
            s.masked_parent_contact = mask_contact(s.parent_contact)
        return ctx


class StudentFormMixin(OwnerQuerysetMixin):
    model = Student
    form_class = StudentForm
    template_name = "students/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["owner"] = self.request.user
        return kwargs

    def _detail_instance(self):
        if self.object and StudentDetail.objects.filter(student=self.object).exists():
            return StudentDetail.objects.get(student=self.object)
        return None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["slot_formset"] = ScheduleSlotFormSet(self.request.POST, instance=self.object)
            ctx["detail_form"] = StudentDetailForm(
                self.request.POST, instance=self._detail_instance(), prefix="detail"
            )
        else:
            ctx["slot_formset"] = ScheduleSlotFormSet(instance=self.object)
            ctx["detail_form"] = StudentDetailForm(instance=self._detail_instance(), prefix="detail")
        ctx["has_subjects"] = Subject.objects.filter(owner=self.request.user).exists()
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        slot_formset = context["slot_formset"]
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        form.save_m2m()
        slot_formset.instance = self.object
        if not slot_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, slot_formset=slot_formset))
        slot_formset.save()
        detail, _ = StudentDetail.objects.get_or_create(student=self.object)
        detail_form = StudentDetailForm(
            self.request.POST, instance=detail, prefix="detail"
        )
        if detail_form.is_valid():
            detail_form.save()
        return HttpResponseRedirect(self.get_success_url())


class StudentCreateView(StudentFormMixin, CreateView):
    success_url = reverse_lazy("student-list")

    def _progress_import_prefill(self) -> dict | None:
        if self.request.GET.get("from_progress_import") != "1":
            return None
        if self.request.method == "POST":
            return None
        draft = self.request.session.get(PROGRESS_IMPORT_SESSION_KEY)
        if not draft:
            return None
        prefill = build_student_prefill(draft.get("meta") or {}, self.request.user)
        if not prefill.get("labels"):
            return None
        return prefill

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        prefill = self._progress_import_prefill()
        if prefill:
            for key, value in prefill["student_fields"].items():
                form.fields[key].initial = value
            if prefill["subject_ids"]:
                form.fields["subjects"].initial = prefill["subject_ids"]
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["slot_formset"] = ScheduleSlotFormSet(self.request.POST)
        else:
            ctx["slot_formset"] = ScheduleSlotFormSet()
        prefill = self._progress_import_prefill()
        if prefill:
            ctx["import_prefill_active"] = True
            ctx["import_prefill_labels"] = prefill["labels"]
            if prefill.get("detail_memo"):
                ctx["detail_form"] = StudentDetailForm(
                    initial={"long_memo": prefill["detail_memo"]},
                    prefix="detail",
                )
        return ctx


class StudentUpdateView(StudentFormMixin, UpdateView):
    def get_success_url(self):
        return reverse("student-detail", kwargs={"pk": self.object.pk})


class StudentDetailView(OwnerQuerysetMixin, DetailView):
    model = Student
    template_name = "students/detail.html"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("subjects", "schedule_slots")

    def get_template_names(self):
        if self.request.GET.get("lesson"):
            return ["students/lesson_detail.html"]
        return ["students/detail.html"]

    def _lesson_detail_url(self, lesson_pk: int) -> str:
        return reverse("student-detail", kwargs={"pk": self.object.pk}) + f"?lesson={lesson_pk}"

    def get_context_data(self, **kwargs):
        from calendar_app.models import Lesson
        from core.timezone_suggest import timezone_label_ko

        ctx = super().get_context_data(**kwargs)
        lesson_id = self.request.GET.get("lesson")
        if lesson_id:
            from zoneinfo import ZoneInfo

            from calendar_app.services import lesson_has_started

            edit_lesson = get_object_or_404(Lesson, pk=lesson_id, student=self.object)
            tz = ZoneInfo(self.object.timezone)
            local_start = edit_lesson.start_datetime.astimezone(tz)
            local_end = edit_lesson.end_datetime.astimezone(tz)
            ctx["edit_lesson"] = edit_lesson
            ctx["lesson_has_started"] = lesson_has_started(edit_lesson)
            ctx["lesson_local_date"] = local_start.date().isoformat()
            ctx["lesson_start_time"] = local_start.strftime("%H:%M")
            ctx["lesson_end_time"] = local_end.strftime("%H:%M")
            return ctx

        ctx["timezone_label"] = timezone_label_ko(self.object.timezone)
        ctx["hourly_rate_display"] = f"{int(self.object.hourly_rate):,}"
        detail, _ = StudentDetail.objects.get_or_create(student=self.object)
        ctx["detail"] = detail
        ctx["history"] = detail.history_entries.all()
        ctx["memo_form"] = StudentDetailForm(instance=detail)
        ctx["history_form"] = GoalHistoryEntryForm()
        ctx["entry_type_choices"] = GoalHistoryEntry.EntryType.choices
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        lesson_id = request.GET.get("lesson")
        if lesson_id:
            return self._post_lesson(request, int(lesson_id))

        detail, _ = StudentDetail.objects.get_or_create(student=self.object)
        action = request.POST.get("action", "memo")

        if action == "memo":
            form = StudentDetailForm(request.POST, instance=detail)
            if form.is_valid():
                form.save()
            return redirect("student-detail", pk=self.object.pk)

        if action == "history_add":
            form = GoalHistoryEntryForm(request.POST)
            if form.is_valid():
                entry = form.save(commit=False)
                entry.detail = detail
                entry.save()
            return redirect("student-detail", pk=self.object.pk)

        if action == "history_edit":
            entry = get_object_or_404(
                GoalHistoryEntry, pk=int(request.POST["entry_id"]), detail__student=self.object
            )
            form = GoalHistoryEntryForm(request.POST, instance=entry)
            if form.is_valid():
                form.save()
            return redirect("student-detail", pk=self.object.pk)

        if action == "history_delete":
            entry = get_object_or_404(
                GoalHistoryEntry, pk=int(request.POST["entry_id"]), detail__student=self.object
            )
            entry.delete()
            return redirect("student-detail", pk=self.object.pk)

        return redirect("student-detail", pk=self.object.pk)

    def _post_lesson(self, request, lesson_id: int):
        from datetime import date, time

        from django.contrib import messages

        from calendar_app.models import Lesson
        from calendar_app.services import save_lesson_detail

        lesson = get_object_or_404(Lesson, pk=lesson_id, student=self.object)
        if request.POST.get("action") == "lesson_update":
            if lesson.status == Lesson.Status.COMPLETED:
                messages.error(request, "완료된 수업은 수정할 수 없습니다. 완료 취소 후 다시 시도하세요.")
                return HttpResponseRedirect(self._lesson_detail_url(lesson.pk))
            try:
                save_lesson_detail(
                    lesson,
                    lesson_content=request.POST.get("lesson_content", ""),
                    lesson_notes=request.POST.get("lesson_notes", ""),
                    on_date=date.fromisoformat(request.POST["lesson_date"]),
                    start_time=time.fromisoformat(request.POST["start_time"]),
                    end_time=time.fromisoformat(request.POST["end_time"]),
                )
            except (ValueError, KeyError) as exc:
                messages.error(request, str(exc))
        return HttpResponseRedirect(self._lesson_detail_url(lesson.pk))


class TimezoneSuggestView(LoginRequiredMixin, View):
    def get(self, request):
        current = request.GET.get("timezone", "")
        return JsonResponse({"suggestions": list_common_timezones(current)})


class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = "students/subjects.html"
    context_object_name = "subjects"

    def get_queryset(self):
        return Subject.objects.filter(owner=self.request.user).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = SubjectForm()
        return ctx

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "update":
            subject = get_object_or_404(
                Subject, pk=int(request.POST["subject_id"]), owner=request.user
            )
            form = SubjectForm(request.POST, instance=subject)
            if form.is_valid():
                form.save()
        else:
            form = SubjectForm(request.POST)
            if form.is_valid():
                Subject.objects.create(owner=request.user, name=form.cleaned_data["name"])
        return self.get(request, *args, **kwargs)


class ProgressHubView(LoginRequiredMixin, ListView):
    model = Student
    template_name = "students/progress_hub.html"
    context_object_name = "students"

    def get_queryset(self):
        return Student.objects.filter(owner=self.request.user).order_by("name")


class ProgressChartView(OwnerQuerysetMixin, DetailView):
    model = Student
    template_name = "students/progress.html"

    def get_context_data(self, **kwargs):
        from calendar_app.models import Lesson
        from zoneinfo import ZoneInfo

        ctx = super().get_context_data(**kwargs)
        tz = ZoneInfo(self.object.timezone)
        rows = []
        for lesson in Lesson.objects.filter(
            student=self.object, status=Lesson.Status.COMPLETED
        ).order_by("lesson_number"):
            local_start = lesson.start_datetime.astimezone(tz)
            weekday = ["월", "화", "수", "목", "금", "토", "일"][local_start.weekday()]
            rows.append(
                {
                    "lesson": lesson,
                    "weekday": weekday,
                    "time": local_start.strftime("%H:%M"),
                }
            )
        ctx["rows"] = rows
        return ctx


class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject
    success_url = reverse_lazy("subject-list")

    def get_queryset(self):
        return Subject.objects.filter(owner=self.request.user)
