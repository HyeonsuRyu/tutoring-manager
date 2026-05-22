from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from calendar_app.models import Lesson
from calendar_app.services import approve_proposal, cancel_lesson, complete_lesson, dismiss_proposal, get_calendar_events
from students.models import Student


class HomeCalendarView(LoginRequiredMixin, TemplateView):
    template_name = "calendar/home.html"


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
        return JsonResponse(get_calendar_events(request.user, range_start, range_end))


class LessonCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk, student__owner=request.user)
        complete_lesson(lesson)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "lessons_completed": lesson.student.lessons_completed})
        return redirect(reverse("student-detail", kwargs={"pk": lesson.student_id}))


class LessonApproveView(LoginRequiredMixin, View):
    def post(self, request):
        slot_id = int(request.POST["schedule_slot_id"])
        on_date = date.fromisoformat(request.POST["date"])
        lesson = approve_proposal(request.user, slot_id, on_date)
        return JsonResponse({"ok": True, "lesson_id": lesson.id})


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
        return redirect(reverse("student-detail", kwargs={"pk": lesson.student_id}))
