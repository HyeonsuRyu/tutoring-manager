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
from students.models import GoalHistoryEntry, Student, StudentDetail, Subject


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["slot_formset"] = ScheduleSlotFormSet(self.request.POST, instance=self.object)
        else:
            ctx["slot_formset"] = ScheduleSlotFormSet(instance=self.object)
        tz = getattr(self.object, "timezone", None) or "Asia/Seoul"
        ctx["timezone_suggestions"] = list_common_timezones(tz)
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
        StudentDetail.objects.get_or_create(student=self.object)
        return HttpResponseRedirect(self.get_success_url())


class StudentCreateView(StudentFormMixin, CreateView):
    success_url = reverse_lazy("student-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["slot_formset"] = ScheduleSlotFormSet(self.request.POST)
        else:
            ctx["slot_formset"] = ScheduleSlotFormSet()
        return ctx


class StudentUpdateView(StudentFormMixin, UpdateView):
    def get_success_url(self):
        return reverse("student-detail", kwargs={"pk": self.object.pk})


class StudentDetailView(OwnerQuerysetMixin, DetailView):
    model = Student
    template_name = "students/detail.html"

    def get_context_data(self, **kwargs):
        from calendar_app.models import Lesson

        ctx = super().get_context_data(**kwargs)
        detail, _ = StudentDetail.objects.get_or_create(student=self.object)
        ctx["detail"] = detail
        ctx["history"] = detail.history_entries.all()
        ctx["memo_form"] = StudentDetailForm(instance=detail)
        ctx["history_form"] = GoalHistoryEntryForm()
        ctx["entry_type_choices"] = GoalHistoryEntry.EntryType.choices
        lesson_id = self.request.GET.get("lesson")
        if lesson_id:
            ctx["edit_lesson"] = get_object_or_404(
                Lesson, pk=lesson_id, student=self.object
            )
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
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

        if action == "lesson_update":
            from calendar_app.models import Lesson

            lesson = get_object_or_404(Lesson, pk=int(request.POST["lesson_id"]), student=self.object)
            lesson.lesson_content = request.POST.get("lesson_content", "")
            lesson.lesson_notes = request.POST.get("lesson_notes", "")
            lesson.save(update_fields=["lesson_content", "lesson_notes"])
            url = reverse("student-detail", kwargs={"pk": self.object.pk}) + f"?lesson={lesson.pk}"
            return HttpResponseRedirect(url)

        return redirect("student-detail", pk=self.object.pk)


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
