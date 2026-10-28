from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache

from .decorators import role_required, login_required_no_cache
from .models import Student, Profile, Course
from .forms import (
    StudentForm,
    RegisterForm,
    UserUpdateForm,
    ProfileUpdateForm,
    TeacherCourseAssignForm,
)


# How long a session should last, per role. This is what makes session
# behaviour genuinely different per user type (rather than just permissions
# being different): Admins and Teachers get longer-lived sessions since
# they're expected to use the system for extended work sessions, while
# Student sessions expire sooner as a lighter-touch security default.
SESSION_LIFETIME_SECONDS = {
    Profile.ROLE_ADMIN: 60 * 60 * 24,      # 24 hours
    Profile.ROLE_TEACHER: 60 * 60 * 12,    # 12 hours
    Profile.ROLE_STUDENT: 60 * 60 * 2,     # 2 hours
}


def _safe_next_url(request, default_url_name="students"):
    """Return the ``next`` GET/POST parameter if it is safe to redirect to,
    otherwise fall back to ``default_url_name``. Prevents open-redirect
    vulnerabilities while still supporting "log in, then return to the page
    you came from" behaviour for @login_required views."""

    next_url = request.POST.get("next") or request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return reverse(default_url_name)


# ---------------------------
# Authentication
# ---------------------------

@never_cache
def login_user(request):

    if request.user.is_authenticated:
        return redirect("students")

    username = ""

    if request.method == "POST":

        username = request.POST.get("username", "")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(request, user)

            # Session management by role: each account type gets a
            # different session lifetime (see SESSION_LIFETIME_SECONDS
            # above). request.session.set_expiry() controls how long this
            # specific session stays valid before Django forces a fresh
            # login, independent of the global SESSION_COOKIE_AGE default.
            role = getattr(user.profile, "role", Profile.ROLE_STUDENT)
            request.session.set_expiry(
                SESSION_LIFETIME_SECONDS.get(role, SESSION_LIFETIME_SECONDS[Profile.ROLE_STUDENT])
            )

            messages.success(
                request,
                f"Welcome back, {user.username}! You're signed in as {user.profile.get_role_display()}."
            )

            return redirect(_safe_next_url(request))

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(request, "login.html", {"username": username})


@never_cache
def logout_user(request):

    if request.method == "POST":

        logout(request)

        messages.success(
            request,
            "Logged out successfully."
        )

        return redirect("login")

    return redirect("students")


@never_cache
def register(request):

    if request.user.is_authenticated:
        return redirect("students")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            # The post_save signal already created a default ("student")
            # Profile — now apply the role the person actually chose on
            # the registration form.
            role = form.cleaned_data["role"]
            user.profile.role = role
            user.profile.save()

            login(request, user)

            request.session.set_expiry(
                SESSION_LIFETIME_SECONDS.get(role, SESSION_LIFETIME_SECONDS[Profile.ROLE_STUDENT])
            )

            messages.success(
                request,
                f"Account created successfully as {user.profile.get_role_display()}."
            )

            return redirect("students")

    else:

        form = RegisterForm()

    return render(
        request,
        "register.html",
        {
            "form": form
        }
    )


# ---------------------------
# Home
# ---------------------------


@login_required_no_cache
def home(request):

    profile = request.user.profile

    # Students get a lightweight personal dashboard rather than
    # school-wide statistics, which are only relevant to staff.
    if profile.role == Profile.ROLE_STUDENT and not request.user.is_superuser:

        own_record = getattr(request.user, "student_record", None)

        return render(
            request,
            "home.html",
            {
                "is_student_view": True,
                "own_record": own_record,
            },
        )

    total_students = Student.objects.count()

    total_courses = Course.objects.count()

    total_cities = Student.objects.values(
        "city"
    ).distinct().count()

    latest_students = Student.objects.select_related("course", "teacher").order_by("-created_at")[:5]

    course_data = Student.objects.values("course__name").annotate(
        total=Count("id")
    ).order_by("-total")

    labels = []
    data = []

    for item in course_data:
        labels.append(item["course__name"])
        data.append(item["total"])

    context = {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_cities": total_cities,
        "latest_students": latest_students,
        "labels": labels,
        "data": data,
    }

    return render(request, "home.html", context)


# ---------------------------
# Student List
# ---------------------------

@login_required_no_cache
def students(request):

    profile = request.user.profile

    # A "Student" account doesn't get to browse the whole roster — only
    # Admins and Teachers manage the full list. A student with a linked
    # record is sent straight to their own detail page instead.
    if profile.role == Profile.ROLE_STUDENT and not request.user.is_superuser:

        own_record = getattr(request.user, "student_record", None)

        if own_record is not None:
            return redirect("student_detail", id=own_record.id)

        messages.info(
            request,
            "No student record is linked to your account yet. "
            "Ask a teacher or admin to link it from the admin panel."
        )

        return redirect("home")

    search = request.GET.get("search", "").strip()
    course_filter = request.GET.get("course", "").strip()

    student_list = Student.objects.select_related("course", "teacher")

    if search:
        student_list = student_list.filter(
            name__icontains=search
        ) | student_list.filter(
            email__icontains=search
        ) | student_list.filter(
            city__icontains=search
        )

    if course_filter:
        student_list = student_list.filter(course_id=course_filter)

    student_list = student_list.order_by("-created_at")

    paginator = Paginator(student_list, 5)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    # Preserve the current query string (minus "page") so pagination links
    # don't silently drop the active search/filter.
    querydict = request.GET.copy()
    querydict.pop("page", None)
    querystring = querydict.urlencode()

    courses = Course.objects.order_by("name")

    context = {

        "students": page_obj,

        "page_obj": page_obj,

        "count": Student.objects.count(),

        "search": search,

        "course_filter": course_filter,

        "courses": courses,

        "querystring": querystring,

    }

    return render(
        request,
        "students.html",
        context,
    )


# ---------------------------
# Student Detail
# ---------------------------

@login_required_no_cache
def student_detail(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    profile = request.user.profile

    is_staff_role = request.user.is_superuser or profile.role in (
        Profile.ROLE_ADMIN, Profile.ROLE_TEACHER
    )

    if not is_staff_role and student.linked_user_id != request.user.id:
        raise PermissionDenied(
            "You can only view your own student record."
        )

    return render(
        request,
        "student_detail.html",
        {
            "student": student
        }
    )


# ---------------------------
# Add Student
# ---------------------------

@role_required(Profile.ROLE_ADMIN, Profile.ROLE_TEACHER)
def add_student(request):

    if request.method == "POST":

        form = StudentForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Student added successfully."
            )

            return redirect("students")

    else:

        form = StudentForm()

    return render(
        request,
        "add_student.html",
        {
            "form": form
        }
    )


# ---------------------------
# Edit Student
# ---------------------------

@role_required(Profile.ROLE_ADMIN, Profile.ROLE_TEACHER)
def edit_student(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    if request.method == "POST":

        form = StudentForm(
            request.POST,
            instance=student
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Student updated successfully."
            )

            return redirect("students")

    else:

        form = StudentForm(
            instance=student
        )

    return render(
        request,
        "edit_student.html",
        {
            "form": form,
            "student": student,
        }
    )


# ---------------------------
# Delete Student
# ---------------------------

@role_required(Profile.ROLE_ADMIN, Profile.ROLE_TEACHER)
def delete_student(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    if request.method == "POST":

        student.delete()

        messages.success(
            request,
            "Student deleted successfully."
        )

        return redirect("students")

    return render(
        request,
        "delete_student.html",
        {
            "student": student
        }
    )


# ---------------------------
# Assign Teacher <-> Courses (Admin only)
# ---------------------------

@role_required(Profile.ROLE_ADMIN)
def assign_teacher_courses(request):

    selected_teacher = None

    if request.method == "POST":

        form = TeacherCourseAssignForm(request.POST)

        if form.is_valid():

            teacher = form.cleaned_data["teacher"]
            courses = form.cleaned_data["courses"]

            teacher.profile.courses.set(courses)

            messages.success(
                request,
                f"Updated course assignments for {teacher.username}."
            )

            return redirect(f"{reverse('assign_teacher_courses')}?teacher={teacher.id}")

    else:

        teacher_id = request.GET.get("teacher")

        initial = {}

        if teacher_id:

            selected_teacher = User.objects.filter(
                id=teacher_id, profile__role=Profile.ROLE_TEACHER
            ).first()

            if selected_teacher is not None:
                initial["teacher"] = selected_teacher.id
                initial["courses"] = selected_teacher.profile.courses.values_list("id", flat=True)

        form = TeacherCourseAssignForm(initial=initial)

    teachers = User.objects.filter(
        profile__role=Profile.ROLE_TEACHER
    ).select_related("profile").order_by("username")

    return render(
        request,
        "assign_teacher_courses.html",
        {
            "form": form,
            "teachers": teachers,
            "selected_teacher": selected_teacher,
        }
    )


# ---------------------------
# Profile
# ---------------------------

@login_required_no_cache
def profile(request):

    return render(
        request,
        "profile.html",
        {
            # Lets the template show *when this specific session* will
            # expire — a concrete, visible proof that session lifetime is
            # tied to the account's role (see SESSION_LIFETIME_SECONDS).
            "session_expiry_date": request.session.get_expiry_date(),
            "session_age_seconds": request.session.get_expiry_age(),
        }
    )


# ---------------------------
# Edit Profile
# ---------------------------

@login_required_no_cache
def edit_profile(request):

    if request.method == "POST":

        user_form = UserUpdateForm(
            request.POST,
            instance=request.user
        )

        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()
            profile_form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("profile")

    else:

        user_form = UserUpdateForm(
            instance=request.user
        )

        profile_form = ProfileUpdateForm(
            instance=request.user.profile
        )

    context = {

        "user_form": user_form,

        "profile_form": profile_form,

    }

    return render(
        request,
        "edit_profile.html",
        context,
    )
