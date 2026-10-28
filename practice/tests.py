from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Student, Profile, Course


def make_course(name="Computer Science"):
    course, _ = Course.objects.get_or_create(name=name)
    return course


class StudentModelTests(TestCase):

    def test_str_returns_name(self):
        student = Student.objects.create(
            name="Jane Doe", age=21, course=make_course(), email="jane@example.com",
            phone="9876543210", city="Pune",
        )
        self.assertEqual(str(student), "Jane Doe")


class CourseModelTests(TestCase):

    def test_str_returns_name(self):
        course = Course.objects.create(name="Data Science", code="DS101")
        self.assertEqual(str(course), "Data Science")

    def test_course_name_must_be_unique(self):
        Course.objects.create(name="Physics")
        with self.assertRaises(Exception):
            Course.objects.create(name="Physics")


class ProfileSignalTests(TestCase):

    def test_profile_created_on_user_creation(self):
        user = User.objects.create_user(username="alice", password="StrongPass123")
        self.assertTrue(Profile.objects.filter(user=user).exists())


class AuthViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="StrongPass123")
        # These tests exercise general auth/CRUD behaviour, not role
        # scoping specifically, so give this user full (Teacher) access.
        self.user.profile.role = Profile.ROLE_TEACHER
        self.user.profile.save()

    def test_students_page_requires_login(self):
        response = self.client.get(reverse("students"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_login_success_redirects_to_students(self):
        response = self.client.post(
            reverse("login"), {"username": "bob", "password": "StrongPass123"}
        )
        self.assertRedirects(response, reverse("students"))

    def test_login_failure_shows_error(self):
        response = self.client.post(
            reverse("login"), {"username": "bob", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_login_failure_message_uses_danger_alert_class(self):
        # Regression test: Django's default "error" message tag doesn't
        # map to any real Bootstrap class (only "alert-danger" exists),
        # so without MESSAGE_TAGS the error would render unstyled/invisible.
        response = self.client.post(
            reverse("login"), {"username": "bob", "password": "wrong"}
        )
        self.assertContains(response, "alert-danger")
        self.assertNotContains(response, "alert-error")

    def test_logout_requires_post(self):
        self.client.login(username="bob", password="StrongPass123")
        response = self.client.get(reverse("logout"))
        # GET should not log the user out (CSRF-safety requires POST).
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get("_auth_user_id"))


class EmailValidationTests(TestCase):
    """Covers the explicit '@' check added on top of Django's built-in
    EmailField validation, across every form that collects an email."""

    def setUp(self):
        self.user = User.objects.create_user(username="carol", password="StrongPass123")
        self.user.profile.role = Profile.ROLE_TEACHER
        self.user.profile.save()
        self.client.login(username="carol", password="StrongPass123")
        self.course = make_course()

    def test_register_rejects_email_without_at_symbol(self):
        # register() redirects already-authenticated users away before
        # even looking at the form, and setUp() leaves the client logged
        # in — so log out first to test the registration form itself.
        self.client.logout()
        response = self.client.post(reverse("register"), {
            "role": "student",
            "username": "noatuser",
            "email": "notanemail.com",
            "password1": "Xk9$mPlanet7Zebra",
            "password2": "Xk9$mPlanet7Zebra",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@")
        self.assertFalse(User.objects.filter(username="noatuser").exists())

    def test_add_student_rejects_email_without_at_symbol(self):
        response = self.client.post(reverse("add_student"), {
            "name": "Bad Email",
            "age": 20,
            "course": self.course.id,
            "email": "bademail.com",
            "phone": "9123456799",
            "city": "Pune",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(name="Bad Email").exists())

    def test_add_student_accepts_valid_email(self):
        response = self.client.post(reverse("add_student"), {
            "name": "Good Email",
            "age": 20,
            "course": self.course.id,
            "email": "good@example.com",
            "phone": "9123456798",
            "city": "Pune",
        })
        self.assertRedirects(response, reverse("students"))
        self.assertTrue(Student.objects.filter(email="good@example.com").exists())


class StudentCRUDTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="carol2", password="StrongPass123")
        self.user.profile.role = Profile.ROLE_TEACHER
        self.user.profile.save()
        self.client.login(username="carol2", password="StrongPass123")
        self.course = make_course("Physics")
        self.other_course = make_course("Mathematics")

    def test_add_student(self):
        response = self.client.post(reverse("add_student"), {
            "name": "John Smith",
            "age": 22,
            "course": self.course.id,
            "email": "john@example.com",
            "phone": "9123456789",
            "city": "Delhi",
        })
        self.assertRedirects(response, reverse("students"))
        self.assertTrue(Student.objects.filter(email="john@example.com").exists())

    def test_edit_student(self):
        student = Student.objects.create(
            name="John Smith", age=22, course=self.course, email="john2@example.com",
            phone="9123456780", city="Delhi",
        )
        response = self.client.post(
            reverse("edit_student", args=[student.id]),
            {
                "name": "John Updated",
                "age": 23,
                "course": self.other_course.id,
                "email": "john2@example.com",
                "phone": "9123456780",
                "city": "Delhi",
            },
        )
        self.assertRedirects(response, reverse("students"))
        student.refresh_from_db()
        self.assertEqual(student.name, "John Updated")
        self.assertEqual(student.course, self.other_course)

    def test_delete_student(self):
        student = Student.objects.create(
            name="Delete Me", age=20, course=self.course, email="delete@example.com",
            phone="9123456781", city="Mumbai",
        )
        response = self.client.post(reverse("delete_student", args=[student.id]))
        self.assertRedirects(response, reverse("students"))
        self.assertFalse(Student.objects.filter(id=student.id).exists())

    def test_invalid_age_rejected(self):
        response = self.client.post(reverse("add_student"), {
            "name": "Bad Age",
            "age": -5,
            "course": self.course.id,
            "email": "badage@example.com",
            "phone": "9123456782",
            "city": "Mumbai",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(email="badage@example.com").exists())

    def test_course_must_be_chosen_from_predefined_list(self):
        # Free-text course values are no longer accepted — only an id of
        # an existing Course row.
        response = self.client.post(reverse("add_student"), {
            "name": "Free Text Course",
            "age": 20,
            "course": "Some Made Up Course",
            "email": "freetext@example.com",
            "phone": "9123456783",
            "city": "Mumbai",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(email="freetext@example.com").exists())


class JWTAPITests(TestCase):
    """Covers the JWT-authenticated API under /api/."""

    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="StrongPass123")
        self.course = make_course()
        self.student = Student.objects.create(
            name="API Student", age=21, course=self.course, email="apistudent@example.com",
            phone="9123456700", city="Delhi",
        )

    def _get_tokens(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "apiuser", "password": "StrongPass123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_obtain_token_with_valid_credentials(self):
        data = self._get_tokens()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_obtain_token_with_invalid_credentials_fails(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "apiuser", "password": "wrong"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_students_list_requires_authentication(self):
        response = self.client.get(reverse("api-student-list"))
        self.assertEqual(response.status_code, 401)

    def test_students_list_with_valid_token(self):
        tokens = self._get_tokens()
        response = self.client.get(
            reverse("api-student-list"),
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_create_student_via_api(self):
        tokens = self._get_tokens()
        response = self.client.post(
            reverse("api-student-list"),
            {
                "name": "New API Student",
                "age": 22,
                "course": self.course.id,
                "email": "newapi@example.com",
                "phone": "9123456701",
                "city": "Mumbai",
            },
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Student.objects.filter(email="newapi@example.com").exists())

    def test_refresh_token_issues_new_access_token(self):
        tokens = self._get_tokens()
        response = self.client.post(
            reverse("token_refresh"),
            {"refresh": tokens["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_logout_blacklists_refresh_token(self):
        tokens = self._get_tokens()
        access = tokens["access"]
        refresh = tokens["refresh"]

        logout_response = self.client.post(
            reverse("api_logout"),
            {"refresh": refresh},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(logout_response.status_code, 205)

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            content_type="application/json",
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_register_via_api(self):
        response = self.client.post(
            reverse("api_register"),
            {
                "username": "brandnewuser",
                "email": "brandnew@example.com",
                "password": "Xk9$mPlanet7Zebra",
                "password2": "Xk9$mPlanet7Zebra",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="brandnewuser").exists())
        # A Profile should have been auto-created by the post_save signal.
        self.assertTrue(Profile.objects.filter(user__username="brandnewuser").exists())


class RoleBasedAccessTests(TestCase):
    """Covers session-based role management: Admin / Teacher / Student."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="roleadmin", password="StrongPass123", email="roleadmin@example.com"
        )
        # superuser gets role="admin" automatically via the post_save signal

        self.teacher = User.objects.create_user(username="roleteacher", password="StrongPass123")
        self.teacher.profile.role = Profile.ROLE_TEACHER
        self.teacher.profile.save()

        self.student_user = User.objects.create_user(username="rolestudent", password="StrongPass123")
        # role defaults to "student" already

        self.other_student_user = User.objects.create_user(username="otherstudent", password="StrongPass123")

        self.course = make_course()
        self.other_course = make_course("Mathematics")

        self.student_record = Student.objects.create(
            name="Linked Student", age=20, course=self.course, email="linked@example.com",
            phone="9123450001", city="Delhi", linked_user=self.student_user,
        )
        self.unrelated_record = Student.objects.create(
            name="Unrelated Student", age=21, course=self.other_course, email="unrelated@example.com",
            phone="9123450002", city="Mumbai",
        )

    def test_superuser_auto_gets_admin_role(self):
        self.assertEqual(self.admin.profile.role, Profile.ROLE_ADMIN)

    def test_new_user_defaults_to_student_role(self):
        self.assertEqual(self.other_student_user.profile.role, Profile.ROLE_STUDENT)

    def test_admin_can_add_student(self):
        self.client.login(username="roleadmin", password="StrongPass123")
        response = self.client.get(reverse("add_student"))
        self.assertEqual(response.status_code, 200)

    def test_teacher_can_add_student(self):
        self.client.login(username="roleteacher", password="StrongPass123")
        response = self.client.get(reverse("add_student"))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_add_student(self):
        self.client.login(username="rolestudent", password="StrongPass123")
        response = self.client.get(reverse("add_student"), follow=True)
        # role_required bounces to "students", which then bounces a
        # Student-role account on to their own linked record.
        self.assertRedirects(response, reverse("student_detail", args=[self.student_record.id]))
        self.assertContains(response, "don&#x27;t have permission")

    def test_student_cannot_edit_or_delete(self):
        self.client.login(username="rolestudent", password="StrongPass123")
        response = self.client.get(reverse("edit_student", args=[self.unrelated_record.id]), follow=True)
        self.assertRedirects(response, reverse("student_detail", args=[self.student_record.id]))

        response = self.client.get(reverse("delete_student", args=[self.unrelated_record.id]), follow=True)
        self.assertRedirects(response, reverse("student_detail", args=[self.student_record.id]))

    def test_student_redirected_to_own_record_from_list(self):
        self.client.login(username="rolestudent", password="StrongPass123")
        response = self.client.get(reverse("students"))
        self.assertRedirects(response, reverse("student_detail", args=[self.student_record.id]))

    def test_student_can_view_own_record(self):
        self.client.login(username="rolestudent", password="StrongPass123")
        response = self.client.get(reverse("student_detail", args=[self.student_record.id]))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_view_others_record(self):
        self.client.login(username="rolestudent", password="StrongPass123")
        response = self.client.get(reverse("student_detail", args=[self.unrelated_record.id]))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_view_any_record(self):
        self.client.login(username="roleteacher", password="StrongPass123")
        response = self.client.get(reverse("student_detail", args=[self.unrelated_record.id]))
        self.assertEqual(response.status_code, 200)

    def test_registration_with_teacher_role(self):
        response = self.client.post(reverse("register"), {
            "role": "teacher",
            "username": "newteacher",
            "email": "newteacher@example.com",
            "password1": "Xk9$mPlanet7Zebra",
            "password2": "Xk9$mPlanet7Zebra",
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username="newteacher")
        self.assertEqual(new_user.profile.role, Profile.ROLE_TEACHER)

    def test_session_expiry_differs_by_role(self):
        # Admin session should be set to 24 hours (86400s), Student to 2
        # hours (7200s) — proving session lifetime genuinely varies by
        # role. Must go through the actual login *view* (not the test
        # client's login() shortcut, which bypasses application code and
        # therefore never calls request.session.set_expiry()).
        self.client.post(reverse("login"), {"username": "roleadmin", "password": "StrongPass123"})
        admin_session_age = self.client.session.get_expiry_age()
        self.client.post(reverse("logout"))

        self.client.post(reverse("login"), {"username": "rolestudent", "password": "StrongPass123"})
        student_session_age = self.client.session.get_expiry_age()

        self.assertGreater(admin_session_age, student_session_age)


class TeacherCourseAssignmentTests(TestCase):
    """Covers assigning teachers to courses, and students to teachers."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="courseadmin", password="StrongPass123", email="courseadmin@example.com"
        )
        self.teacher = User.objects.create_user(username="assignteacher", password="StrongPass123")
        self.teacher.profile.role = Profile.ROLE_TEACHER
        self.teacher.profile.save()

        self.other_teacher = User.objects.create_user(username="otherteacher", password="StrongPass123")
        self.other_teacher.profile.role = Profile.ROLE_TEACHER
        self.other_teacher.profile.save()

        self.student_user = User.objects.create_user(username="assignstudent", password="StrongPass123")

        self.course_a = make_course("Course A")
        self.course_b = make_course("Course B")

    def test_page_requires_admin(self):
        self.client.login(username="assignteacher", password="StrongPass123")
        response = self.client.get(reverse("assign_teacher_courses"), follow=True)
        self.assertContains(response, "don&#x27;t have permission")

    def test_admin_can_assign_courses_to_teacher(self):
        self.client.login(username="courseadmin", password="StrongPass123")
        response = self.client.post(reverse("assign_teacher_courses"), {
            "teacher": self.teacher.id,
            "courses": [self.course_a.id, self.course_b.id],
        })
        self.assertEqual(response.status_code, 302)

        self.teacher.profile.refresh_from_db()
        assigned = set(self.teacher.profile.courses.values_list("id", flat=True))
        self.assertEqual(assigned, {self.course_a.id, self.course_b.id})

    def test_assigning_one_teacher_does_not_affect_another(self):
        self.teacher.profile.courses.set([self.course_a])
        self.other_teacher.profile.courses.set([self.course_b])

        self.client.login(username="courseadmin", password="StrongPass123")
        self.client.post(reverse("assign_teacher_courses"), {
            "teacher": self.teacher.id,
            "courses": [self.course_b.id],
        })

        self.teacher.profile.refresh_from_db()
        self.other_teacher.profile.refresh_from_db()
        self.assertEqual(set(self.teacher.profile.courses.values_list("id", flat=True)), {self.course_b.id})
        self.assertEqual(set(self.other_teacher.profile.courses.values_list("id", flat=True)), {self.course_b.id})

    def test_student_can_be_assigned_a_teacher(self):
        self.client.login(username="courseadmin", password="StrongPass123")
        response = self.client.post(reverse("add_student"), {
            "name": "Assigned Student",
            "age": 20,
            "course": self.course_a.id,
            "teacher": self.teacher.id,
            "email": "assigned@example.com",
            "phone": "9123456790",
            "city": "Pune",
        })
        self.assertRedirects(response, reverse("students"))
        student = Student.objects.get(email="assigned@example.com")
        self.assertEqual(student.teacher, self.teacher)

    def test_student_field_only_lists_teacher_role_users(self):
        from .forms import StudentForm
        form = StudentForm()
        teacher_queryset_usernames = set(form.fields["teacher"].queryset.values_list("username", flat=True))
        self.assertIn("assignteacher", teacher_queryset_usernames)
        self.assertNotIn("assignstudent", teacher_queryset_usernames)


class NoCacheAfterLogoutTests(TestCase):
    """Regression test for the browser Back-button issue: protected pages
    must never be servable from the browser's cache after logout, or
    pressing Back can briefly show stale authenticated content instead of
    forcing a fresh (redirected-to-login) request."""

    def setUp(self):
        self.user = User.objects.create_user(username="cachetest", password="StrongPass123")
        self.client.login(username="cachetest", password="StrongPass123")

    def _assert_uncacheable(self, response):
        cache_control = response.headers.get("Cache-Control", "")
        self.assertIn("no-store", cache_control)

    def test_students_page_is_not_cacheable(self):
        response = self.client.get(reverse("students"))
        self._assert_uncacheable(response)

    def test_home_page_is_not_cacheable(self):
        response = self.client.get(reverse("home"))
        self._assert_uncacheable(response)

    def test_profile_page_is_not_cacheable(self):
        response = self.client.get(reverse("profile"))
        self._assert_uncacheable(response)

    def test_login_page_is_not_cacheable(self):
        self.client.logout()
        response = self.client.get(reverse("login"))
        self._assert_uncacheable(response)

    def test_role_protected_page_is_not_cacheable(self):
        self.user.profile.role = Profile.ROLE_TEACHER
        self.user.profile.save()
        response = self.client.get(reverse("add_student"))
        self._assert_uncacheable(response)
