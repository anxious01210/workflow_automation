# accounts/models.py
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from .managers import UserManager

ROLE_STUDENT = "role_student"
ROLE_FACULTY = "role_faculty"
ROLE_STAFF = "role_staff"          # org staff (HR/Finance/etc.), NOT Django is_staff
ROLE_PARENT = "role_guardian"       # keep legacy var name, value is guardian
ROLE_EXTERNAL = "role_external"
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

    # auto-maintained by signals when a user has >=1 GuardianChild rows
    is_guardian = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def _normalize_fields(self):
        if self.email:
            self.email = self.email.strip().lower()
            try:
                self.email_domain = self.email.split("@", 1)[1].lower()
            except IndexError:
                self.email_domain = None
        else:
            self.email_domain = None

        if self.manager_email:
            self.manager_email = self.manager_email.strip().lower()

        if self.department:
            self.department = self.department.strip()
        if self.job_title:
            self.job_title = self.job_title.strip()
        if self.tenant_id:
            self.tenant_id = self.tenant_id.strip()
        if self.azure_oid:
            self.azure_oid = self.azure_oid.strip()

        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()

    def save(self, *args, **kwargs):
        self._normalize_fields
        super().save(*args, **kwargs)


# --- Guardian–Child link ---
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

    guardian = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="children_links"
    )
    child = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="guardian_links"
    )

    # relation labels from each side (keep your current design)
    guardian_role = models.CharField(max_length=20, choices=GUARDIAN_ROLE_CHOICES, default="guardian")
    child_relation = models.CharField(max_length=20, choices=CHILD_REL_CHOICES, default="child")

    # useful flags (optional but handy)
    is_primary = models.BooleanField(default=False)      # at most one per child? (see optional unique constraint below)
    can_pickup = models.BooleanField(default=True)

    # optional validity window
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Guardian–child link"
        verbose_name_plural = "Guardian–child links"
        unique_together = ("guardian", "child")
        constraints = [
            models.CheckConstraint(check=~Q(guardian=F("child")), name="pc_guardian_not_child"),
            # Uncomment to enforce only one primary guardian per child:
            # models.UniqueConstraint(fields=["child"], condition=Q(is_primary=True), name="uniq_primary_guardian_per_child"),
        ]
        indexes = [
            models.Index(fields=["guardian"]),
            models.Index(fields=["child"]),
            models.Index(fields=["child", "is_primary"]),
        ]
        ordering = ["child", "-is_primary", "guardian_role", "guardian_id"]

    def __str__(self):
        return f"{self.guardian.email} → {self.child.email} ({self.guardian_role})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.guardian_id and self.child_id and self.guardian_id == self.child_id:
            raise ValidationError({"guardian": "Guardian and child cannot be the same user."})
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    @property
    def active(self):
        from django.utils import timezone
        today = timezone.localdate()
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
