from django.contrib import admin

from students.models import GoalHistoryEntry, ScheduleSlot, Student, StudentDetail, Subject


class ScheduleSlotInline(admin.TabularInline):
    model = ScheduleSlot
    extra = 1


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "grade", "owner", "lessons_completed")
    list_filter = ("owner",)
    inlines = [ScheduleSlotInline]


admin.site.register(Subject)
admin.site.register(StudentDetail)
admin.site.register(GoalHistoryEntry)
