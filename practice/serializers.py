from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Student, Profile


class StudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Student
        fields = [
            "id",
            "name",
            "age",
            "course",
            "email",
            "phone",
            "city",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ["profile_picture", "bio", "joined_date"]
        read_only_fields = ["joined_date"]


class UserSerializer(serializers.ModelSerializer):
    """Read/update serializer for the logged-in user's own account."""

    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]
        read_only_fields = ["id", "username"]


class RegisterSerializer(serializers.ModelSerializer):
    """Creates a new User account via the API. Reuses Django's own
    password validators so API and template registration enforce the
    exact same password rules."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate_email(self, email):
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
