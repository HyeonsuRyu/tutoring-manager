import json
from datetime import date, time, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from calendar_app.models import Lesson
from calendar_app.services import (
    LessonNotStartedError,
    approve_proposal,
    cancel_lesson,
    complete_lesson,
    create_manual_lesson,
    dismiss_proposal,
    get_calendar_events,
    resolve_student_for_owner,
    update_lesson_content,
)
from students.models import Student


class HomeCalendarView(LoginRequiredMixin, TemplateView):
    template_name = "calendar/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        students = Student.objects.filter(owner=self.request.user).order_by("name")
        ctx["calendar_students_json"] = json.dumps(
            [{"id": s.id, "name": s.name} for s in students],
            ensure_ascii=False,
        )
        return ctx


class CalendarEventsJsonView(LoginRequiredMixin, View):
    """Session-authenticated calendar JSON for FullCalendar."""

    def get(self, request):
        start_s = request.GET.get("start", "")[:10]
        end_s = request.GET.get("end", "")[:10]
        if not start_s:
            today = date.today()
            range_start = today - timedelta(days=today.weekday())
            range_end = range_start + timedelta(days=13)
        else:
            range_start = date.fromisoformat(start_s)
            range_end = date.fromisoformat(end_s)
        response = JsonResponse(get_calendar_events(request.user, range_start, range_end))
        response["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response["Pragma"] = "no-cache"
        return response


class LessonCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk, student__owner=request.user)
        update_lesson_content(
            lesson,
            lesson_content=request.POST.get("lesson_content", ""),
            lesson_notes=request.POST.get("lesson_notes", ""),
        )
        try:
            complete_lesson(lesson)
        except LessonNotStartedError:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "message": "아직 수업 전입니다."}, status=400)
            messages.error(request, "아직 수업 전입니다.")
            return redirect(
                reverse("student-detail", kwargs={"pk": lesson.student_id})
                + f"?lesson={lesson.pk}"
            )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "lessons_completed": lesson.student.lessons_completed})
        return redirect(
            reverse("student-detail", kwargs={"pk": lesson.student_id})
            + f"?lesson={lesson.pk}"
        )


class LessonApproveView(LoginRequiredMixin, View):
    def post(self, request):
        slot_id = int(request.POST["schedule_slot_id"])
        on_date = date.fromisoformat(request.POST["date"])
        lesson = approve_proposal(request.user, slot_id, on_date)
        return JsonResponse({"ok": True, "lesson_id": lesson.id})


class LessonManualCreateView(LoginRequiredMixin, View):
    """POST: add a lesson from the calendar + button."""

    def post(self, request):
        try:
            on_date = date.fromisoformat(request.POST.get("date", ""))
            start_time = time.fromisoformat(request.POST.get("start_time", ""))
            end_time = time.fromisoformat(request.POST.get("end_time", ""))
            student = resolve_student_for_owner(
                request.user,
                student_id=int(request.POST["student_id"])
                if request.POST.get("student_id")
                else None,
                student_name=request.POST.get("student_name", ""),
            )
            lesson = create_manual_lesson(
                request.user,
                student=student,
                course_name=request.POST.get("course_name", ""),
                on_date=on_date,
                start_time=start_time,
                end_time=end_time,
            )
        except (ValueError, KeyError, Student.DoesNotExist) as exc:
            return JsonResponse({"ok": False, "message": str(exc)}, status=400)
        return JsonResponse({"ok": True, "lesson_id": lesson.id, "lesson_number": lesson.lesson_number})


class LessonDismissView(LoginRequiredMixin, View):
    def post(self, request):
        slot_id = int(request.POST["schedule_slot_id"])
        on_date = date.fromisoformat(request.POST["date"])
        dismiss_proposal(request.user, slot_id, on_date)
        return JsonResponse({"ok": True})


class LessonCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk, student__owner=request.user)
        makeup_raw = request.POST.get("makeup_date", "").strip()
        makeup_date = date.fromisoformat(makeup_raw) if makeup_raw else None
        cancel_lesson(
            lesson,
            cancelled_by=request.POST.get("cancelled_by", "student"),
            cancel_reason=request.POST.get("cancel_reason", ""),
            makeup_status=request.POST.get("makeup_status", "undecided"),
            makeup_date=makeup_date,
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True})
        return redirect(
            reverse("student-detail", kwargs={"pk": lesson.student_id})
            + f"?lesson={lesson.pk}"
        )
