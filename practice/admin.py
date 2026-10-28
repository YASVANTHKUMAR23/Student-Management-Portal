from django.contrib import admin

from .models import Student, Profile, Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "student_count", "teacher_count")
    search_fields = ("name", "code")
    ordering = ("name",)

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Students enrolled"

    def teacher_count(self, obj):
        return obj.teachers.count()
    teacher_count.short_description = "Teachers assigned"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "age", "course", "teacher", "email", "phone", "city", "linked_user", "created_at")
    list_filter = ("course", "city", "teacher")
    search_fields = ("name", "email", "phone", "city")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("linked_user", "teacher")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "joined_date")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")
    filter_horizontal = ("courses",)
