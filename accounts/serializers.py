from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        from django.conf import settings

        data = super().validate(attrs)
        if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "") == "mandatory":
            from allauth.account.models import EmailAddress
            from rest_framework import serializers

            if not EmailAddress.objects.filter(user=self.user, verified=True).exists():
                raise serializers.ValidationError(
                    {"detail": "Email not verified", "code": "email_not_verified"}
                )
        return data
