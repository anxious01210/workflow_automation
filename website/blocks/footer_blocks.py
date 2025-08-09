# website/blocks/footer_blocks.py
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class LinkBlock(blocks.StructBlock):
    text = blocks.CharBlock()
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)
    new_tab = blocks.BooleanBlock(required=False, help_text="Open in new tab")

    class Meta:
        icon = "link"
        label = "Link"


class LinkGroupBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    links = blocks.ListBlock(LinkBlock(), help_text="Add links for this group")

    class Meta:
        icon = "list-ul"
        label = "Link group"


class SocialLinksBlock(blocks.StructBlock):
    source = blocks.ChoiceBlock(choices=[("settings", "Use UX settings"), ("manual", "Manual list")],
                                default="settings")
    # IMPORTANT: list-of-tuples for StructBlock fields (not dict)
    items = blocks.ListBlock(
        blocks.StructBlock([
            ("label", blocks.CharBlock()),
            ("url", blocks.URLBlock()),
        ]),
        required=False,
    )

    class Meta:
        icon = "site"
        label = "Social links"


class LogoBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False, help_text="If blank, the site name will be used")
    link_to_home = blocks.BooleanBlock(required=False, default=True)

    class Meta:
        icon = "image"
        label = "Logo"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    alt = blocks.CharBlock(required=False)

    class Meta:
        icon = "image"
        label = "Image"


class CTAButtonBlock(blocks.StructBlock):
    text = blocks.CharBlock()
    url = blocks.URLBlock()
    style = blocks.ChoiceBlock(choices=[("primary", "Primary"), ("secondary", "Secondary"), ("ghost", "Ghost")],
                               default="primary")

    class Meta:
        icon = "plus"
        label = "CTA button"


class AddressBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    lines = blocks.ListBlock(blocks.CharBlock(label="Line"), required=False)
    phone = blocks.CharBlock(required=False)
    email = blocks.CharBlock(required=False)

    class Meta:
        icon = "placeholder"
        label = "Address"


class DividerBlock(blocks.StructBlock):
    thickness = blocks.IntegerBlock(default=1, min_value=1, max_value=8)

    class Meta:
        icon = "horizontalrule"
        label = "Divider"


class SpacerBlock(blocks.StructBlock):
    height_px = blocks.IntegerBlock(default=16, min_value=0, max_value=200)

    class Meta:
        icon = "arrows-up-down"
        label = "Spacer"


class EmbedBlock(blocks.StructBlock):
    url = blocks.URLBlock(help_text="Paste an embed/iframe URL")

    class Meta:
        icon = "media"
        label = "Embed"


class FooterStreamBlock(blocks.StreamBlock):
    link_group = LinkGroupBlock()
    social = SocialLinksBlock()
    logo = LogoBlock()
    image = ImageBlock()
    cta = CTAButtonBlock()
    address = AddressBlock()
    divider = DividerBlock()
    spacer = SpacerBlock()
    richtext = blocks.RichTextBlock(features=["bold", "italic", "link", "ol", "ul", "hr", "h3", "h4", "h5", "h6"])
    embed = EmbedBlock()

    class Meta:
        label = "Footer content"
