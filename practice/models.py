from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.contrib.auth.models import User


phone_validator = RegexValidator(
    regex=r"^\+?\d{7,15}$",
    message="Enter a valid phone number (7-15 digits, optionally starting with '+').",
)


class Course(models.Model):
    """A predefined course/programme that students enrol in and teachers
    are assigned to teach. Managed by Admins via the Django admin panel —
    students and teachers can only *choose* from this list, not type
    arbitrary free text."""

    name = models.CharField(max_length=150, unique=True)

    code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Optional short code, e.g. 'CSE101'.",
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):

    name = models.CharField(max_length=100)

    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)]
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="students",
        help_text="Choose from the predefined list of courses.",
    )

    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=15,
        validators=[phone_validator],
    )

    city = models.CharField(max_length=100)

    # The teacher responsible for this student. Restricted to Users whose
    # Profile.role is "teacher" (enforced in StudentForm, not at the DB
    # level, since limit_choices_to can't reach across the Profile
    # relation in a SQLite-friendly way).
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taught_students",
        help_text="The teacher assigned to this student.",
    )

    # Optional link back to the User account of the student this record
    # belongs to. Lets a "Student" role account see their own record
    # without being able to browse everyone else's.
    linked_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_record",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return self.name


class Profile(models.Model):

    ROLE_ADMIN = "admin"
    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_TEACHER, "Teacher"),
        (ROLE_STUDENT, "Student"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
    )

    # Only meaningful when role == "teacher": which courses this teacher
    # is assigned to teach. A teacher can be assigned multiple courses.
    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name="teachers",
        help_text="Courses this teacher is assigned to (Teacher accounts only).",
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        default="default.png"
    )

    bio = models.TextField(
        blank=True
    )

    joined_date = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
