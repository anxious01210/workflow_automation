from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "email", "first_name", "last_name", "department", "job_title",
            "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
        )
