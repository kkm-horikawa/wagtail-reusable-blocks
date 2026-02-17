"""Serializers for wagtail-reusable-blocks API."""

from typing import Any

from django.utils.text import slugify
from rest_framework import fields as drf_fields
from rest_framework import serializers

from wagtail_reusable_blocks.models import ReusableBlock


class StreamFieldField(drf_fields.Field):  # type: ignore[misc]
    """Custom DRF field for Wagtail StreamField serialization.

    Converts StreamValue to JSON-serializable list on read,
    and accepts JSON list on write.
    """

    def to_representation(self, value: Any) -> list[Any]:
        """Convert StreamValue to a JSON-serializable list."""
        if not value:
            return []
        request = self.context.get("request")
        return value.stream_block.get_api_representation(value, request)  # type: ignore[no-any-return]

    def to_internal_value(self, data: Any) -> list[Any]:
        """Accept a JSON list of stream blocks."""
        if data is None:
            return []
        if not isinstance(data, list):
            raise serializers.ValidationError(
                "Content must be a list of stream blocks."
            )
        return data


class ReusableBlockSerializer(serializers.ModelSerializer):  # type: ignore[misc]
    """Serializer for ReusableBlock model with StreamField support.

    Handles:
    - StreamField content as JSON (read/write)
    - Auto-generated slug from name
    - Circular reference validation
    - Revision creation on save
    """

    content = StreamFieldField(required=False, default=list)

    class Meta:
        model = ReusableBlock
        fields = [
            "id",
            "name",
            "slug",
            "content",
            "live",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "live"]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness, excluding the current instance on update."""
        instance = self.instance
        qs = ReusableBlock.objects.filter(slug=value)
        if instance is not None:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A reusable block with this slug already exists."
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Run model-level validation including circular reference detection."""
        if not attrs.get("slug") and attrs.get("name"):
            attrs["slug"] = slugify(attrs["name"])

        # validate_slug only runs for explicit input; auto-generated slugs need checking here
        slug = attrs.get("slug")
        if slug:
            qs = ReusableBlock.objects.filter(slug=slug)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"slug": "A reusable block with this slug already exists."}
                )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> ReusableBlock:
        """Create a new ReusableBlock and save an initial revision."""
        instance = ReusableBlock(**validated_data)
        instance.full_clean()
        instance.save()
        instance.save_revision()
        return instance

    def update(
        self, instance: ReusableBlock, validated_data: dict[str, Any]
    ) -> ReusableBlock:
        """Update a ReusableBlock and save a revision."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        instance.save_revision()
        return instance
