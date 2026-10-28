from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [

    path("", views.home, name="home"),

    path("login/", views.login_user, name="login"),

    path("register/", views.register, name="register"),

    path("logout/", views.logout_user, name="logout"),

    path("students/", views.students, name="students"),

    path("student/<int:id>/", views.student_detail, name="student_detail"),

    path("add-student/", views.add_student, name="add_student"),

    path("edit-student/<int:id>/", views.edit_student, name="edit_student"),

    path("delete-student/<int:id>/", views.delete_student, name="delete_student"),

    path("profile/", views.profile, name="profile"),

    path("edit-profile/", views.edit_profile, name="edit_profile"),

    path("assign-teacher-courses/", views.assign_teacher_courses, name="assign_teacher_courses"),

    # ---------------------------------------------------------------
    # Password change (for logged-in users)
    # ---------------------------------------------------------------
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="password_change.html",
            success_url=reverse_lazy("password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="password_change_done.html"
        ),
        name="password_change_done",
    ),

    # ---------------------------------------------------------------
    # Password reset ("forgot password", for logged-out users)
    # ---------------------------------------------------------------
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset_form.html",
            email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

]
