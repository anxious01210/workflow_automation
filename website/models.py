from modelcluster.models import ClusterableModel
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.images.models import Image
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class HomePage(Page):
    intro = RichTextField(blank=True)
    content = StreamField([
        ("hero", blocks.StructBlock([
            ("heading", blocks.CharBlock()),
            ("subheading", blocks.TextBlock(required=False)),
            ("image", ImageChooserBlock(required=False)),
            ("cta_text", blocks.CharBlock(required=False)),
            ("cta_url", blocks.URLBlock(required=False)),
        ])),
        ("hero_slider", blocks.ListBlock(blocks.StructBlock([
            ("image", ImageChooserBlock(required=False)),
            ("heading", blocks.CharBlock(required=False)),
            ("subheading", blocks.TextBlock(required=False)),
            ("cta_text", blocks.CharBlock(required=False)),
            ("cta_url", blocks.URLBlock(required=False)),
        ]))),
        ("feature_list", blocks.ListBlock(blocks.StructBlock([
            ("title", blocks.CharBlock()),
            ("text", blocks.TextBlock(required=False)),
            ("icon", blocks.CharBlock(required=False)),
        ]))),
        ("richtext", blocks.RichTextBlock()),
    ], use_json_field=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("content"),
    ]


class StandardPage(Page):
    body = StreamField([
        ("richtext", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
    ], use_json_field=True, blank=True)

    content_panels = Page.content_panels + [FieldPanel("body")]


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)
    subpage_types = ["website.BlogPage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request):
        ctx = super().get_context(request)
        posts = BlogPage.objects.live().public().order_by("-first_published_at")
        tag = request.GET.get("tag")
        if tag:
            posts = posts.filter(tags__name=tag)
        ctx.update({"posts": posts})
        return ctx


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250, blank=True)
    body = StreamField([
        ("richtext", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
        ("quote", blocks.BlockQuoteBlock()),
    ], use_json_field=True)
    tags = models.ManyToManyField("taggit.Tag", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]


class NavMenuItem(ClusterableModel):
    """Helper base so we can reuse if you add a footer menu later."""

    class Meta:
        abstract = True


@register_setting
class NavigationSettings(BaseSiteSetting, ClusterableModel):
    logo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    panels = [
        FieldPanel("logo"),
        InlinePanel("items", label="Menu items"),
    ]


class NavigationItem(models.Model):
    settings = ParentalKey(NavigationSettings, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=50)
    link_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    external_url = models.URLField(blank=True)
    new_tab = models.BooleanField(default=False)
    sort = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel("title"),
        FieldPanel("link_page"),
        FieldPanel("external_url"),
        FieldPanel("new_tab"),
        FieldPanel("sort"),
    ]

    class Meta:
        ordering = ["sort", "id"]

    def __str__(self):
        return self.title

    @property
    def url(self):
        if self.link_page:
            return self.link_page.url
        return self.external_url or "#"


# --- Site UX settings (announcement bar + footer menus/socials) ---
@register_setting
class UXSettings(BaseSiteSetting, ClusterableModel):
    announcement_text = models.CharField(max_length=200, blank=True)
    show_announcement = models.BooleanField(default=False)

    footer_groups_per_row = models.PositiveIntegerField(default=3,
                                                        help_text="How many link groups per row on desktop (e.g., 3).")
    footer_gap_px = models.PositiveIntegerField(default=24, help_text="Gap between groups in pixels.")
    footer_pad_x_px = models.PositiveIntegerField(default=12,
                                                  help_text="Horizontal padding (px) inside the footer container.")
    footer_pad_y_px = models.PositiveIntegerField(default=40,
                                                  help_text="Vertical padding (px) for the main footer section.")

    panels = [
        MultiFieldPanel([
            FieldPanel("show_announcement"),
            FieldPanel("announcement_text"),
        ], heading="Announcement bar"),

        # ⬇⬇ ADD THIS BLOCK ⬇⬇
        MultiFieldPanel([
            FieldPanel("footer_groups_per_row"),
            FieldPanel("footer_gap_px"),
            FieldPanel("footer_pad_x_px"),
            FieldPanel("footer_pad_y_px"),
        ], heading="Footer layout"),
        # ⬆⬆ ADD THIS BLOCK ⬆⬆

        InlinePanel("footer_groups", label="Footer groups"),
        InlinePanel("social_links", label="Social links"),
    ]


# --- New hierarchical groups (editable names) ---
class FooterGroup(ClusterableModel):
    settings = ParentalKey("website.UXSettings", on_delete=models.CASCADE, related_name="footer_groups")
    title = models.CharField(max_length=80)
    sort = models.PositiveIntegerField(default=0)

    panels = [FieldPanel("title"), FieldPanel("sort"), InlinePanel("links", label="Links")]

    class Meta:
        ordering = ["sort", "id"]

    def __str__(self):
        return self.title


class FooterItem(models.Model):
    group = ParentalKey(FooterGroup, on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=80)
    link_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    external_url = models.URLField(blank=True)
    sort = models.PositiveIntegerField(default=0)

    panels = [FieldPanel("title"), FieldPanel("link_page"), FieldPanel("external_url"), FieldPanel("sort")]

    class Meta:
        ordering = ["sort", "id"]

    def __str__(self):
        return self.title

    @property
    def url(self):
        return self.link_page.url if self.link_page else (self.external_url or "#")


class SocialLink(models.Model):
    settings = ParentalKey(UXSettings, on_delete=models.CASCADE, related_name="social_links")
    label = models.CharField(max_length=20, help_text="e.g., X, Facebook, LinkedIn")
    url = models.URLField()
    sort = models.PositiveIntegerField(default=0)

    panels = [FieldPanel("label"), FieldPanel("url"), FieldPanel("sort")]

    class Meta:
        ordering = ["sort", "id"]

    def __str__(self):
        return self.label
