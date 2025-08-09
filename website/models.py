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
from .blocks.footer_blocks import FooterStreamBlock


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

    # footer_groups_per_row = models.PositiveIntegerField(default=3,
    #                                                     help_text="How many link groups per row on desktop (e.g., 3).")
    # footer_gap_px = models.PositiveIntegerField(default=24, help_text="Gap between groups in pixels.")
    # footer_pad_x_px = models.PositiveIntegerField(default=12,
    #                                               help_text="Horizontal padding (px) inside the footer container.")
    # footer_pad_y_px = models.PositiveIntegerField(default=40,
    #                                               help_text="Vertical padding (px) for the main footer section.")

    panels = [
        MultiFieldPanel([
            FieldPanel("show_announcement"),
            FieldPanel("announcement_text"),
        ], heading="Announcement bar"),

        # ⬇⬇ ADD THIS BLOCK ⬇⬇
        # MultiFieldPanel([
        #     FieldPanel("footer_groups_per_row"),
        #     FieldPanel("footer_gap_px"),
        #     FieldPanel("footer_pad_x_px"),
        #     FieldPanel("footer_pad_y_px"),
        # ], heading="Footer layout"),
        # ⬆⬆ ADD THIS BLOCK ⬆⬆

        # InlinePanel("footer_groups", label="Footer groups"),
        # InlinePanel("social_links", label="Social links"),
    ]


# # --- New hierarchical groups (editable names) ---
# class FooterGroup(ClusterableModel):
#     settings = ParentalKey("website.UXSettings", on_delete=models.CASCADE, related_name="footer_groups")
#     title = models.CharField(max_length=80)
#     sort = models.PositiveIntegerField(default=0)
#
#     panels = [FieldPanel("title"), FieldPanel("sort"), InlinePanel("links", label="Links")]
#
#     class Meta:
#         ordering = ["sort", "id"]
#
#     def __str__(self):
#         return self.title
#
#
# class FooterItem(models.Model):
#     group = ParentalKey(FooterGroup, on_delete=models.CASCADE, related_name="links")
#     title = models.CharField(max_length=80)
#     link_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
#     external_url = models.URLField(blank=True)
#     sort = models.PositiveIntegerField(default=0)
#
#     panels = [FieldPanel("title"), FieldPanel("link_page"), FieldPanel("external_url"), FieldPanel("sort")]
#
#     class Meta:
#         ordering = ["sort", "id"]
#
#     def __str__(self):
#         return self.title
#
#     @property
#     def url(self):
#         return self.link_page.url if self.link_page else (self.external_url or "#")


# class SocialLink(models.Model):
#     settings = ParentalKey(UXSettings, on_delete=models.CASCADE, related_name="social_links")
#     label = models.CharField(max_length=20, help_text="e.g., X, Facebook, LinkedIn")
#     url = models.URLField()
#     sort = models.PositiveIntegerField(default=0)
#
#     panels = [FieldPanel("label"), FieldPanel("url"), FieldPanel("sort")]
#
#     class Meta:
#         ordering = ["sort", "id"]
#
#     def __str__(self):
#         return self.label

CONTAINER_CHOICES = [("container", "Container (max width)"), ("full", "Full width (edge‑to‑edge)")]
BG_STYLE_CHOICES = [("none", "None"), ("solid", "Solid color"), ("gradient", "Gradient"), ("image", "Image")]


@register_setting
class FooterSettings(BaseSiteSetting, ClusterableModel):
    # Global background / overlay
    container = models.CharField(max_length=16, choices=CONTAINER_CHOICES, default="container")
    bg_style = models.CharField(max_length=12, choices=BG_STYLE_CHOICES, default="none")
    bg_color = models.CharField(max_length=32, blank=True, help_text="#hex or any CSS color")
    gradient_from = models.CharField(max_length=32, blank=True)
    gradient_to = models.CharField(max_length=32, blank=True)
    bg_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+"
    )
    overlay_color = models.CharField(max_length=32, blank=True, help_text="rgba() or #hex")
    overlay_opacity = models.PositiveIntegerField(default=0, help_text="0‑100%")

    # Section 1 — top strip
    s1_enabled = models.BooleanField(default=True)
    s1_container = models.CharField(max_length=16, choices=CONTAINER_CHOICES, default="container")
    s1_cols_md = models.PositiveIntegerField(default=2)
    s1_cols_lg = models.PositiveIntegerField(default=4)
    s1_gap = models.PositiveIntegerField(default=24)
    s1_pad_x = models.PositiveIntegerField(default=12)
    s1_pad_y = models.PositiveIntegerField(default=24)
    s1_content = StreamField(FooterStreamBlock(), use_json_field=True, blank=True)

    # Section 2 — main links grid
    s2_enabled = models.BooleanField(default=True)
    s2_container = models.CharField(max_length=16, choices=CONTAINER_CHOICES, default="container")
    s2_cols_md = models.PositiveIntegerField(default=3)
    s2_cols_lg = models.PositiveIntegerField(default=5)
    s2_gap = models.PositiveIntegerField(default=24)
    s2_pad_x = models.PositiveIntegerField(default=12)
    s2_pad_y = models.PositiveIntegerField(default=32)
    s2_content = StreamField(FooterStreamBlock(), use_json_field=True, blank=True)

    # Section 3 — contact / addresses strip
    s3_enabled = models.BooleanField(default=True)
    s3_container = models.CharField(max_length=16, choices=CONTAINER_CHOICES, default="container")
    s3_cols_md = models.PositiveIntegerField(default=2)
    s3_cols_lg = models.PositiveIntegerField(default=3)
    s3_gap = models.PositiveIntegerField(default=24)
    s3_pad_x = models.PositiveIntegerField(default=12)
    s3_pad_y = models.PositiveIntegerField(default=24)
    s3_content = StreamField(FooterStreamBlock(), use_json_field=True, blank=True)

    # Section 4 — bottom bar
    s4_enabled = models.BooleanField(default=True)
    s4_container = models.CharField(max_length=16, choices=CONTAINER_CHOICES, default="container")
    s4_cols_md = models.PositiveIntegerField(default=2)
    s4_cols_lg = models.PositiveIntegerField(default=2)
    s4_gap = models.PositiveIntegerField(default=12)
    s4_pad_x = models.PositiveIntegerField(default=12)
    s4_pad_y = models.PositiveIntegerField(default=16)
    s4_content = StreamField(FooterStreamBlock(), use_json_field=True, blank=True)

    panels = [
        MultiFieldPanel([
            FieldPanel("container"),
            FieldPanel("bg_style"),
            FieldPanel("bg_color"),
            FieldPanel("gradient_from"),
            FieldPanel("gradient_to"),
            FieldPanel("bg_image"),
            FieldPanel("overlay_color"),
            FieldPanel("overlay_opacity"),
        ], heading="Global background & overlay"),

        MultiFieldPanel([
            FieldPanel("s1_enabled"), FieldPanel("s1_container"), FieldPanel("s1_cols_md"), FieldPanel("s1_cols_lg"),
            FieldPanel("s1_gap"), FieldPanel("s1_pad_x"), FieldPanel("s1_pad_y"), FieldPanel("s1_content")
        ], heading="Section 1"),

        MultiFieldPanel([
            FieldPanel("s2_enabled"), FieldPanel("s2_container"), FieldPanel("s2_cols_md"), FieldPanel("s2_cols_lg"),
            FieldPanel("s2_gap"), FieldPanel("s2_pad_x"), FieldPanel("s2_pad_y"), FieldPanel("s2_content")
        ], heading="Section 2"),

        MultiFieldPanel([
            FieldPanel("s3_enabled"), FieldPanel("s3_container"), FieldPanel("s3_cols_md"), FieldPanel("s3_cols_lg"),
            FieldPanel("s3_gap"), FieldPanel("s3_pad_x"), FieldPanel("s3_pad_y"), FieldPanel("s3_content")
        ], heading="Section 3"),

        MultiFieldPanel([
            FieldPanel("s4_enabled"), FieldPanel("s4_container"), FieldPanel("s4_cols_md"), FieldPanel("s4_cols_lg"),
            FieldPanel("s4_gap"), FieldPanel("s4_pad_x"), FieldPanel("s4_pad_y"), FieldPanel("s4_content")
        ], heading="Section 4"),
    ]
