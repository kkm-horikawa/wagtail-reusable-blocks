"""Serializers for wagtail-reusable-blocks API."""

from typing import Any

from django.utils.text import slugify
from rest_framework import serializers

from wagtail_reusable_blocks.models import ReusableBlock


class ReusableBlockSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for ReusableBlock model with StreamField support.

    Handles:
    - StreamField content as JSON (read/write)
    - Auto-generated slug from name
    - Circular reference validation
    - Revision creation on save
    """

    content = serializers.JSONField(required=False, default=list)

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
