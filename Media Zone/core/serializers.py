# core/serializers.py
from rest_framework import serializers
from core.models import MediaItem, SearchHistory, User
from django.contrib.auth.hashers import make_password
import re


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "user_name", "user_password", "user_email", "user_role"]

    def create(self, validated_data):
        # Hash password before saving
        validated_data["user_password"] = make_password(validated_data["user_password"])
        user = User.objects.create(**validated_data)
        return user

    def validate_user_password(self, value):
        # Password validation (optional but good practice)
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long"
            )
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter"
            )
        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError(
                "Password must contain at least one digit"
            )
        return value


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ["id", "user", "query", "media_type", "searched_at"]
        read_only_fields = [
            "id",
            "searched_at",
        ]  # Make 'id' and 'searched_at' read-only

    def validate_media_type(self, value):
        """Ensure that the media_type is valid (either 'image', 'audio', or 'video')"""
        if value not in ["image", "audio", "video"]:
            raise serializers.ValidationError("Invalid media type.")
        return value


class MediaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaItem
        fields = [
            "id",
            "user",
            "query",
            "media_type",
            "url",
            "title",
            "thumbnail",
            "fetched_at",
        ]
        read_only_fields = ["id", "fetched_at"]  # Make 'id' and 'fetched_at' read-only

    def validate_media_type(self, value):
        """Validate media type. Can be extended to restrict certain media types if needed."""
        if not value:
            raise serializers.ValidationError("Media type cannot be empty.")
        return value

    def validate_url(self, value):
        """Ensure the URL is a valid format."""
        if not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("Invalid URL format.")
        return value
