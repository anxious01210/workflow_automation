# accounts/models.py
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from .managers import UserManager

ROLE_STUDENT = "role_student"
ROLE_FACULTY = "role_faculty"
ROLE_STAFF = "role_staff"  # your org staff (HR/Finance/etc.), NOT Django is_staff
ROLE_PARENT = "role_guardian"
ROLE_EXTERNAL = "role_external"  # registered public users
ROLE_STUDENTS = "role_students"
ROLE_PRIMARY = "role_primary"
ROLE_SECONDARY = "role_secondary"
ROLE_ADMINISTRATION = "role_administration"

ROLE_SLUGS = {ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT, ROLE_EXTERNAL}


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    identity_source = models.CharField(
        max_length=20,
        choices=[("LOCAL", "Local"), ("AZURE", "Azure"), ("GOOGLE", "Google")],
        default="LOCAL",
    )
    azure_oid = models.CharField(max_length=64, blank=True, null=True)
    tenant_id = models.CharField(max_length=64, blank=True, null=True)

    manager_email = models.EmailField(blank=True, null=True)
    department = models.CharField(max_length=128, blank=True, null=True)
    job_title = models.CharField(max_length=128, blank=True, null=True)

    email_domain = models.CharField(max_length=128, blank=True, null=True)
    licenses = models.JSONField(default=list, blank=True)
    groups_cache = models.JSONField(default=list, blank=True)

    is_guardian = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    # --- Normalizers (one place, easy to extend) ---
    def _normalize_fields(self):
        # Email + domain
        if self.email:
            self.email = self.email.strip().lower()
            try:
                self.email_domain = self.email.split("@", 1)[1].lower()
            except IndexError:
                self.email_domain = None
        else:
            self.email_domain = None

        # Optional emails
        if self.manager_email:
            self.manager_email = self.manager_email.strip().lower()

        # Trim strings (don’t change case—orgs may care about capitalization)
        if self.department:
            self.department = self.department.strip()
        if self.job_title:
            self.job_title = self.job_title.strip()
        if self.tenant_id:
            self.tenant_id = self.tenant_id.strip()
        if self.azure_oid:
            self.azure_oid = self.azure_oid.strip()
        # Names: AbstractUser has null=False here; never save None
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()

    def save(self, *args, **kwargs):
        self._normalize_fields()
        super().save(*args, **kwargs)


# accounts/models.py (add below)
# class GuardianChild(models.Model):
#     guardian = models.ForeignKey(User, on_delete=models.CASCADE, related_name="children_links")
#     child  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="guardian_links")
#     relation = models.CharField(max_length=32, default="guardian")  # father/mother/guardian etc.
#
#     class Meta:
#         unique_together = ("guardian", "child")

from django.db import models
from django.db.models import Q, F


class GuardianChild(models.Model):
    GUARDIAN_ROLE_CHOICES = [
        ("guardian", "Guardian"),
        ("mother", "Mother"),
        ("father", "Father"),
        ("uncle", "Uncle"),
        ("aunt", "Aunt"),
        ("other", "Other"),
    ]
    CHILD_REL_CHOICES = [
        ("child", "Child"),
        ("daughter", "Daughter"),
        ("son", "Son"),
        ("ward", "Ward"),
        ("other", "Other"),
    ]

    guardian = models.ForeignKey(User, on_delete=models.CASCADE, related_name="children_links")
    child  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="guardian_links")
    guardian_role  = models.CharField(max_length=20, choices=GUARDIAN_ROLE_CHOICES, default="guardian")
    child_relation = models.CharField(max_length=20, choices=CHILD_REL_CHOICES, default="child")
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ("guardian", "child")
        constraints = [
            models.CheckConstraint(check=~models.Q(guardian=models.F("child")), name="pc_guardian_not_child"),
        ]
        verbose_name = "Guardian–child link"
        verbose_name_plural = "Guardian–child links"
