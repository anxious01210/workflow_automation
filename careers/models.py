from django.db import models
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet

@register_snippet
class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name

class JobIndexPage(Page):
    subpage_types = ["careers.JobPostingPage"]
    parent_page_types = ["website.HomePage", "website.StandardPage"]

    def get_context(self, request):
        ctx = super().get_context(request)
        qs = JobPostingPage.objects.live().public()
        dept = request.GET.get("dept")
        if dept:
            qs = qs.filter(department__name=dept)
        ctx["jobs"] = qs.order_by("-first_published_at")
        ctx["departments"] = Department.objects.all()
        return ctx

class JobPostingPage(Page):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=120, blank=True)
    employment_type = models.CharField(max_length=60, blank=True, help_text="e.g., Full-time, Part-time")
    posted_at = models.DateField(auto_now_add=True)
    closing_date = models.DateField(null=True, blank=True)
    salary_range = models.CharField(max_length=120, blank=True)
    apply_url = models.URLField(blank=True)

    description = StreamField([
        ("richtext", blocks.RichTextBlock()),
        ("list", blocks.ListBlock(blocks.CharBlock(label="Bullet"))),
    ], use_json_field=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("department"),
        FieldPanel("location"),
        FieldPanel("employment_type"),
        FieldPanel("salary_range"),
        FieldPanel("closing_date"),
        FieldPanel("apply_url"),
        FieldPanel("description"),
    ]

    @property
    def is_open(self):
        from django.utils import timezone
        return not self.closing_date or self.closing_date >= timezone.localdate()
