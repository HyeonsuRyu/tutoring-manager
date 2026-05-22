from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.forms import SignupForm
from accounts.serializers import EmailTokenObtainPairSerializer


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
