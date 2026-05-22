from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from reports.services import get_weekly_report, list_week_options


class WeeklyReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/weekly.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()
        iso = today.isocalendar()
        year = int(self.request.GET.get("year", iso[0]))
        week = int(self.request.GET.get("week", iso[1]))
        ctx["year"] = year
        ctx["week"] = week
        ctx["week_options"] = list_week_options(year)["weeks"]
        ctx["years"] = range(year - 1, year + 2)
        ctx["report"] = get_weekly_report(self.request.user, year, week)
        return ctx
