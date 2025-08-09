# accounts/admin.py
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django import forms
from django.db.models import Count
from django.contrib.admin.helpers import ActionForm
from django.db import models as dj_models

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import GuardianChild, ROLE_STUDENT, ROLE_FACULTY, ROLE_STAFF, ROLE_PARENT

User = get_user_model()

# ----- Guardian–child admin -----
class GuardianChildForm(forms.ModelForm):
    class Meta:
        model = GuardianChild
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("guardian") and cleaned.get("child") and cleaned["guardian"] == cleaned["child"]:
            raise forms.ValidationError("Guardian and child cannot be the same user.")
        return cleaned

@admin.register(GuardianChild)
class GuardianChildAdmin(admin.ModelAdmin):
    form = GuardianChildForm
    list_display = (
        "guardian_email", "guardian_role",
        "child_email", "child_relation",
        "is_primary", "can_pickup",
        "active_badge", "short_note",
    )
    search_fields = (
        "guardian__email","guardian__first_name","guardian__last_name",
        "child__email","child__first_name","child__last_name","note"
    )
    list_filter = ("guardian_role","child_relation","is_primary","can_pickup","guardian__email_domain","child__email_domain")
    ordering = ("child__email","-is_primary","guardian__email")
    autocomplete_fields = ("guardian","child")
    formfield_overrides = { dj_models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows":2})} }

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("guardian","child")

    @admin.display(ordering="guardian__email", description="Guardian")
    def guardian_email(self, obj): return obj.guardian.email

    @admin.display(ordering="child__email", description="Child")
    def child_email(self, obj): return obj.child.email

    @admin.display(description="Active")
    def active_badge(self, obj): return "✅" if obj.active else "⛔"

    @admin.display(description="Note")
    def short_note(self, obj):
        return (obj.note[:70] + "…") if obj.note and len(obj.note) > 70 else (obj.note or "—")


# ---- Optional inlines on the User page (toggle) ----
USE_USER_INLINES = False

class ChildrenInline(admin.TabularInline):
    """Shown on a Guardian user page."""
    model = GuardianChild
    fk_name = "guardian"
    extra = 0
    verbose_name = "Child"
    verbose_name_plural = "Children"
    fields = ("child", "child_relation", "is_primary", "can_pickup", "start_date", "end_date", "note")
    autocomplete_fields = ("child",)
    show_change_link = True
    formfield_overrides = { dj_models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows":2})} }

class GuardiansInline(admin.TabularInline):
    """Shown on a Child (student) user page."""
    model = GuardianChild
    fk_name = "child"
    extra = 0
    verbose_name = "Guardian"
    verbose_name_plural = "Guardians"
    fields = ("guardian", "guardian_role", "is_primary", "can_pickup", "start_date", "end_date", "note")
    autocomplete_fields = ("guardian",)
    show_change_link = True
    formfield_overrides = { dj_models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows":2})} }


# ---- Bulk link action: “Link selected users as Children → chosen Guardian” ----
class LinkToGuardianActionForm(ActionForm):
    guardian = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Guardian",
    )
    guardian_role = forms.ChoiceField(choices=GuardianChild.GUARDIAN_ROLE_CHOICES, required=False, initial="guardian", label="Guardian role")
    child_relation = forms.ChoiceField(choices=GuardianChild.CHILD_REL_CHOICES, required=False, initial="child", label="Child relation")

def _make_add_to_group_action(group):
    def action(modeladmin, request, queryset, *, _g=group):
        n = 0
        for u in queryset:
            u.groups.add(_g)
            n += 1
        modeladmin.message_user(request, f"Added {n} users to '{_g.name}'.", level=messages.SUCCESS)
    action.__name__ = f"add_to_group_{group.id}"
    action.short_description = f"Add to group: {group.name}"
    return action

def _make_remove_from_group_action(group):
    def action(modeladmin, request, queryset, *, _g=group):
        n = 0
        for u in queryset:
            if _g in u.groups.all():
                u.groups.remove(_g)
                n += 1
        modeladmin.message_user(request, f"Removed {n} users from '{_g.name}'.", level=messages.SUCCESS)
    action.__name__ = f"remove_from_group_{group.id}"
    action.short_description = f"Remove from group: {group.name}"
    return action

class DynamicGroupActionsMixin:
    def get_actions(self, request):
        actions = super().get_actions(request)
        for g in Group.objects.all().order_by("name"):
            add_fn = _make_add_to_group_action(g)
            rem_fn = _make_remove_from_group_action(g)
            actions[add_fn.__name__] = (add_fn, add_fn.__name__, add_fn.short_description)
            actions[rem_fn.__name__] = (rem_fn, rem_fn.__name__, rem_fn.short_description)
        return actions

class UserAdmin(DynamicGroupActionsMixin, DjangoUserAdmin):
    action_form = LinkToGuardianActionForm
    actions = ["activate_selected", "deactivate_selected", "link_as_children_to_guardian"]
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = (
        "email", "first_name", "last_name", "department", "job_title", "is_active",
        "identity_source", "email_domain","children_count", "guardians_count", "group_names",
    )
    search_fields = ("email", "first_name", "last_name", "department", "job_title")
    ordering = ("email",)
    list_filter = ("is_active", "identity_source", "email_domain", "department", "job_title", "groups")
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "department", "job_title")}),
        ("Directory", {"fields": ("identity_source", "azure_oid", "tenant_id", "manager_email", "email_domain")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser", "groups")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _children_count=Count("children_links", distinct=True),
            _guardians_count=Count("guardian_links", distinct=True),
        ).prefetch_related("groups")

    @admin.display(ordering="_children_count", description="Children")
    def children_count(self, obj): return obj._children_count

    @admin.display(ordering="_guardians_count", description="Guardians")
    def guardians_count(self, obj): return obj._guardians_count

    @admin.display(description="Groups")
    def group_names(self, obj):
        return ", ".join(obj.groups.values_list("name", flat=True)) or "—"

    def activate_selected(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f"Activated {n} users.", level=messages.SUCCESS)
    activate_selected.short_description = "Activate selected users"

    def deactivate_selected(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {n} users.", level=messages.WARNING)
    deactivate_selected.short_description = "Deactivate selected users"

    if USE_USER_INLINES:
        inlines = [ChildrenInline, GuardiansInline]

    @admin.action(description="Link selected users as Children → chosen Guardian")
    def link_as_children_to_guardian(self, request, queryset):
        guardian_id = request.POST.get("guardian")
        guardian = User.objects.filter(pk=guardian_id).first()
        g_role = request.POST.get("guardian_role") or "guardian"
        c_rel = request.POST.get("child_relation") or "child"

        if not guardian:
            self.message_user(request, "Pick a Guardian in the action form above the list.", level=messages.ERROR)
            return

        created = skipped = 0
        for child in queryset:
            if child.pk == guardian.pk:
                skipped += 1
                continue
            obj, was_new = GuardianChild.objects.get_or_create(
                guardian=guardian, child=child,
                defaults={"guardian_role": g_role, "child_relation": c_rel},
            )
            created += int(was_new)

        msg = f"Linked {created} children to {guardian.email}."
        if skipped:
            msg += f" Skipped {skipped} self-links."
        self.message_user(request, msg, level=messages.SUCCESS)

# Re-register to ensure OUR admin class is used
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)
