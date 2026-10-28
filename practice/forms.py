from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Student, Profile, Course


def validate_email_has_at_symbol(value):
    """Explicit, friendly check that the email contains an '@'. Django's
    EmailField already validates the overall format, but this gives a
    clearer, specific error message for the single most common typo
    (forgetting the '@') instead of a generic 'enter a valid email'."""

    if "@" not in value:
        raise forms.ValidationError(
            "Enter a valid email address — it must contain an '@' symbol (e.g. name@example.com)."
        )


class BootstrapFormMixin:
    """Adds Bootstrap ``form-control`` styling to every field automatically
    so templates can keep using the simple ``{{ form.as_p }}`` rendering
    while still looking consistent with the rest of the UI."""

    def _apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")

            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"

            widget.attrs["class"] = (existing + " " + css_class).strip()

            if field.label and not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("placeholder", field.label)


class StudentForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:
        model = Student

        fields = [
            "name",
            "age",
            "course",
            "teacher",
            "email",
            "phone",
            "city"
        ]

        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "e.g. +919876543210"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["course"].queryset = Course.objects.order_by("name")
        self.fields["course"].empty_label = "-- Select a course --"

        # Only Teacher-role accounts should show up as assignable
        # teachers. "teacher" is optional (blank=True on the model), so a
        # student can be added before a teacher is assigned.
        self.fields["teacher"].queryset = User.objects.filter(
            profile__role=Profile.ROLE_TEACHER
        ).order_by("username")
        self.fields["teacher"].empty_label = "-- No teacher assigned yet --"
        self.fields["teacher"].required = False

        self._apply_bootstrap_classes()

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Name cannot be empty.")
        return name

    def clean_email(self):
        email = self.cleaned_data["email"]
        validate_email_has_at_symbol(email)
        return email


class RegisterForm(BootstrapFormMixin, UserCreationForm):

    email = forms.EmailField(required=True)

    # Self-registration is only ever allowed as Teacher or Student.
    # "Admin" accounts are never self-serve — they're created via
    # `createsuperuser` or promoted by an existing admin, so a stray
    # sign-up form can't be used to grant admin access.
    role = forms.ChoiceField(
        choices=[
            (Profile.ROLE_STUDENT, "Student"),
            (Profile.ROLE_TEACHER, "Teacher"),
        ],
        initial=Profile.ROLE_STUDENT,
        help_text="Choose the account type you're registering as.",
    )

    class Meta:

        model = User

        fields = (
            "username",
            "email",
            "password1",
            "password2"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Move "role" to the front so it reads naturally on the form.
        self.order_fields(["role", "username", "email", "password1", "password2"])
        self._apply_bootstrap_classes()

    def clean_email(self):
        email = self.cleaned_data["email"]
        validate_email_has_at_symbol(email)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:

        model = User

        fields = [
            "username",
            "email"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_email(self):
        email = self.cleaned_data["email"]
        validate_email_has_at_symbol(email)
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:

        model = Profile

        fields = [
            "profile_picture",
            "bio"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()
        # The file input needs its own Bootstrap class, not "form-control"
        # appended twice.
        self.fields["profile_picture"].widget.attrs["class"] = "form-control"
        self.fields["bio"].widget.attrs["rows"] = 4


class TeacherCourseAssignForm(BootstrapFormMixin, forms.Form):
    """Admin-only form: pick a teacher, then pick which course(s) they're
    assigned to teach. Both fields render as dropdowns/multi-selects
    populated from the database — no free typing."""

    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role=Profile.ROLE_TEACHER).order_by("username"),
        empty_label="-- Select a teacher --",
        label="Teacher",
    )

    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.order_by("name"),
        widget=forms.SelectMultiple,
        required=False,
        label="Assigned courses",
        help_text="Hold Ctrl (Cmd on Mac) to select multiple courses.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()
        self.fields["courses"].widget.attrs["size"] = 8
