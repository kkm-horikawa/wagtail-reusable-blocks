"""ImageBlock for displaying images with responsive format support."""

from typing import TYPE_CHECKING

from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageChooserBlock

if TYPE_CHECKING:
    from wagtail.blocks import StructBlock as StructBlockType
else:
    StructBlockType = StructBlock  # type: ignore[misc,assignment]


class ImageBlock(StructBlockType):  # type: ignore[misc]
    """Image block with responsive format support.

    Renders images with responsive format support (AVIF > WebP > JPEG fallback)
    using Wagtail's {% picture %} tag.

    Usage:
        >>> from wagtail_reusable_blocks.blocks import ImageBlock
        >>> body = StreamField([
        ...     ('image', ImageBlock()),
        ... ])

    Attributes:
        image: The image to display (Wagtail ImageChooserBlock)

    Template:
        Uses 'wagtail_reusable_blocks/blocks/image.html' by default.
        Override to add lightbox or other features.
    """

    image = ImageChooserBlock(
        required=True,
        label="Image",
        help_text="Select an image to display",
    )

    class Meta:
        template = "wagtail_reusable_blocks/blocks/image.html"
        icon = "image"
        label = "Image"
        help_text = "Image with responsive format support"
