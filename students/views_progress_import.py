import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from students.models import Student
from students.progress_import_apply import apply_progress_import, validate_import_row
from students.progress_xls import draft_from_parse, parse_progress_xls

SESSION_KEY = "progress_import_draft"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def _lesson_payload(row: dict) -> dict:
    return {
        "date": row["date"],
        "start_time": row.get("start_time") or "",
        "end_time": row.get("end_time") or "",
        "lesson_content": row.get("lesson_content") or "",
        "lesson_notes": row.get("lesson_notes") or "",
    }


class ProgressImportUploadView(LoginRequiredMixin, View):
    template_name = "students/progress_import_upload.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            messages.error(request, "엑셀 파일을 선택해 주세요.")
            return redirect("progress-import")
        if not upload.name.lower().endswith((".xls", ".xlsx")):
            messages.error(request, "진도차트.xls 형식의 파일을 업로드해 주세요.")
            return redirect("progress-import")
        if upload.size > MAX_UPLOAD_BYTES:
            messages.error(request, "파일 크기는 5MB 이하여야 합니다.")
            return redirect("progress-import")
        try:
            raw = upload.read()
            meta, lessons = parse_progress_xls(raw)
        except Exception:
            messages.error(request, "엑셀 파일을 읽을 수 없습니다. 진도차트 양식인지 확인해 주세요.")
            return redirect("progress-import")
        if not lessons:
            messages.warning(request, "가져올 수업 데이터가 없습니다. 표(5행 이후)를 확인해 주세요.")
            return redirect("progress-import")
        request.session[SESSION_KEY] = draft_from_parse(meta, lessons)
        return redirect("progress-import-review")


class ProgressImportReviewView(LoginRequiredMixin, View):
    template_name = "students/progress_import_review.html"

    def get(self, request):
        draft = request.session.get(SESSION_KEY)
        if not draft:
            messages.info(request, "먼저 엑셀 파일을 업로드해 주세요.")
            return redirect("progress-import")
        students = Student.objects.filter(owner=request.user).order_by("name")
        suggested = draft["meta"].get("student_name", "").strip()
        return render(
            request,
            self.template_name,
            {
                "draft": draft,
                "students": students,
                "suggested_name": suggested,
            },
        )


class ProgressImportApplyView(LoginRequiredMixin, View):
    def post(self, request):
        draft = request.session.get(SESSION_KEY)
        if not draft:
            return JsonResponse(
                {"ok": False, "error": "가져오기 세션이 만료되었습니다. 다시 업로드해 주세요."},
                status=400,
            )
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": "요청 형식이 올바르지 않습니다."}, status=400)

        student_id = payload.get("student_id")
        if not student_id:
            return JsonResponse({"ok": False, "error": "학생을 선택해 주세요."}, status=400)
        student = Student.objects.filter(pk=student_id, owner=request.user).first()
        if not student:
            return JsonResponse({"ok": False, "error": "학생을 찾을 수 없습니다."}, status=400)

        course_name = (draft.get("meta") or {}).get("subject") or ""
        single = payload.get("single") is True
        draft_lesson_id = (payload.get("draft_lesson_id") or "").strip()

        if single:
            row = payload.get("lesson")
            if not row:
                return JsonResponse({"ok": False, "error": "수업 데이터가 없습니다."}, status=400)
            err = validate_import_row(row)
            if err:
                return JsonResponse({"ok": False, "error": err}, status=400)
            try:
                apply_progress_import(student, [_lesson_payload(row)], course_name=course_name)
            except ValueError as exc:
                return JsonResponse({"ok": False, "error": str(exc)}, status=400)
            except Exception:
                return JsonResponse({"ok": False, "error": "저장 중 오류가 발생했습니다."}, status=500)

            if draft_lesson_id:
                draft["lessons"] = [
                    lesson for lesson in draft["lessons"] if lesson.get("id") != draft_lesson_id
                ]
                request.session[SESSION_KEY] = draft
                request.session.modified = True

            remaining = len(draft.get("lessons") or [])
            progress_url = reverse("student-progress", kwargs={"pk": student.pk})
            return JsonResponse(
                {
                    "ok": True,
                    "remaining": remaining,
                    "progress_url": progress_url,
                    "done": remaining == 0,
                }
            )

        rows = payload.get("lessons") or []
        if not rows:
            return JsonResponse({"ok": False, "error": "적용할 수업이 없습니다."}, status=400)
        for row in rows:
            err = validate_import_row(row)
            if err:
                return JsonResponse({"ok": False, "error": err}, status=400)
        try:
            count = apply_progress_import(student, rows, course_name=course_name)
        except ValueError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        except Exception:
            return JsonResponse({"ok": False, "error": "저장 중 오류가 발생했습니다."}, status=500)
        request.session.pop(SESSION_KEY, None)
        messages.success(request, f"{count}개의 완료 수업을 등록했습니다.")
        return JsonResponse(
            {
                "ok": True,
                "redirect": reverse("student-progress", kwargs={"pk": student.pk}),
                "count": count,
            }
        )


class ProgressImportTemplateDownloadView(LoginRequiredMixin, View):
    def get(self, request):
        from django.conf import settings

        path = settings.BASE_DIR / "resources" / "excel_templates" / "진도차트.xls"
        if not path.exists():
            return HttpResponse("템플릿 파일이 없습니다.", status=404)
        content = path.read_bytes()
        response = HttpResponse(
            content,
            content_type="application/vnd.ms-excel",
        )
        response["Content-Disposition"] = 'attachment; filename="진도차트.xls"'
        return response
