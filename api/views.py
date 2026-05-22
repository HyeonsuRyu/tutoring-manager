from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    ApproveProposalSerializer,
    CancelLessonSerializer,
    DismissProposalSerializer,
    LessonSerializer,
    StudentDetailSerializer,
    StudentListSerializer,
    StudentSerializer,
    SubjectSerializer,
)
from calendar_app.models import Lesson
from calendar_app.services import (
    approve_proposal,
    cancel_lesson,
    complete_lesson,
    dismiss_proposal,
    get_calendar_events,
)
from reports.services import get_weekly_report, list_week_options
from students.models import Student, StudentDetail, Subject


class StandardPagination(PageNumberPagination):
    page_size = 50


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Subject.objects.filter(owner=self.request.user).order_by("name")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StudentViewSet(viewsets.ModelViewSet):
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Student.objects.filter(owner=self.request.user).prefetch_related(
            "subjects", "schedule_slots"
        )
        sort = self.request.query_params.get("sort", "name")
        if sort == "grade":
            return qs.order_by("grade", "name")
        return qs.order_by("name")

    def get_serializer_class(self):
        if self.action == "list":
            return StudentListSerializer
        return StudentSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StudentDetailView(APIView):
    def get_student(self, request, pk):
        return get_object_or_404(Student, pk=pk, owner=request.user)

    def get(self, request, pk):
        student = self.get_student(request, pk)
        detail, _ = StudentDetail.objects.get_or_create(student=student)
        return Response(StudentDetailSerializer(detail).data)

    def patch(self, request, pk):
        student = self.get_student(request, pk)
        detail, _ = StudentDetail.objects.get_or_create(student=student)
        serializer = StudentDetailSerializer(detail, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CalendarEventsView(APIView):
    def get(self, request):
        start_s = request.query_params.get("start")
        end_s = request.query_params.get("end")
        if not start_s or not end_s:
            return Response(
                {"detail": "start and end query params required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        range_start = date.fromisoformat(start_s[:10])
        range_end = date.fromisoformat(end_s[:10])
        return Response(get_calendar_events(request.user, range_start, range_end))


class LessonViewSet(viewsets.GenericViewSet):
    serializer_class = LessonSerializer

    def get_queryset(self):
        return Lesson.objects.filter(student__owner=self.request.user).select_related("student")

    def get_lesson(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        lesson = self.get_lesson(pk)
        complete_lesson(lesson)
        lesson.refresh_from_db()
        lesson.student.refresh_from_db()
        return Response(
            {
                "lesson": LessonSerializer(lesson).data,
                "lessons_completed": lesson.student.lessons_completed,
            }
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        lesson = self.get_lesson(pk)
        ser = CancelLessonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cancel_lesson(lesson, **ser.validated_data)
        return Response(LessonSerializer(lesson).data)

    def partial_update(self, request, pk=None):
        from calendar_app.services import reschedule_lesson
        from django.utils.dateparse import parse_datetime

        lesson = self.get_lesson(pk)
        start_raw = request.data.get("start_datetime")
        end_raw = request.data.get("end_datetime")
        if start_raw:
            start = parse_datetime(start_raw)
            end = parse_datetime(end_raw) if end_raw else None
            if start:
                try:
                    reschedule_lesson(lesson, start_datetime=start, end_datetime=end)
                except ValueError as exc:
                    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
                lesson.refresh_from_db()
        serializer = LessonSerializer(lesson, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update(self, request, pk=None):
        return self.partial_update(request, pk)


class LessonCreateView(APIView):
    """POST /lessons/ — approve proposal."""

    def post(self, request):
        ser = ApproveProposalSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lesson = approve_proposal(
            request.user,
            ser.validated_data["schedule_slot_id"],
            ser.validated_data["date"],
        )
        return Response(LessonSerializer(lesson).data, status=status.HTTP_201_CREATED)


class ProposalDismissView(APIView):
    def post(self, request):
        ser = DismissProposalSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        dismissal = dismiss_proposal(
            request.user,
            ser.validated_data["schedule_slot_id"],
            ser.validated_data["date"],
        )
        return Response({"id": dismissal.id}, status=status.HTTP_201_CREATED)


class WeeklyReportView(APIView):
    def get(self, request):
        year = int(request.query_params.get("year", date.today().isocalendar()[0]))
        week = int(request.query_params.get("week", date.today().isocalendar()[1]))
        return Response(get_weekly_report(request.user, year, week))


class WeeklyWeeksView(APIView):
    def get(self, request):
        year = int(request.query_params.get("year", date.today().isocalendar()[0]))
        return Response(list_week_options(year))
