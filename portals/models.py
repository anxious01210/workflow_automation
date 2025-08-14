from django.db import models

class PortalAccess(models.Model):
    """
    Anchor model to host portal permissions via Meta.permissions.
    Stores no business data.
    """
    class Meta:
        verbose_name = "Portal Access"
        verbose_name_plural = "Portal Access"
        permissions = [
            ("portal_access", "Can access the unified portal"),
            ("portal_admin", "Can administer the portal"),
            ("appointments_view", "Can view appointments in portal"),
            ("leave_submit", "Can submit leave requests in portal"),
            ("purchase_submit", "Can submit purchase requests in portal"),
        ]

    def __str__(self):
        return "Portal Access Permissions"
