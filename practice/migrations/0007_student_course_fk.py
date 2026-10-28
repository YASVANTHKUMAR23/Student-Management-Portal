import django.db.models.deletion
from django.db import migrations, models


def backfill_course_fk(apps, schema_editor):
    """For every existing Student, find (or create) a matching Course row
    by name and point the new course_fk field at it, so no existing data
    is lost when the free-text 'course' field is replaced by a dropdown.
    Legacy free-text values that don't match a predefined course become
    their own Course row automatically (an Admin can rename/merge them
    later via /admin/ if desired)."""

    Student = apps.get_model("practice", "Student")
    Course = apps.get_model("practice", "Course")

    for student in Student.objects.all():
        old_value = (student.course or "").strip()

        if not old_value:
            course, _ = Course.objects.get_or_create(
                name="Undeclared",
                defaults={"code": None},
            )
        else:
            course = Course.objects.filter(name__iexact=old_value).first()
            if course is None:
                course = Course.objects.create(name=old_value)

        student.course_fk = course
        student.save(update_fields=["course_fk"])


def noop_reverse(apps, schema_editor):
    # Nothing to reverse — the old text field is gone by the time this
    # would run in reverse.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('practice', '0006_course'),
    ]

    operations = [
        # 1. Add the new FK column (nullable for now, so backfill can run).
        migrations.AddField(
            model_name='student',
            name='course_fk',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='students',
                to='practice.course',
            ),
        ),

        # 2. Populate it from the old free-text 'course' column.
        migrations.RunPython(backfill_course_fk, noop_reverse),

        # 3. Drop the old free-text column.
        migrations.RemoveField(
            model_name='student',
            name='course',
        ),

        # 4. Rename the new column into its place.
        migrations.RenameField(
            model_name='student',
            old_name='course_fk',
            new_name='course',
        ),

        # 5. Now that every row has a value, make it required.
        migrations.AlterField(
            model_name='student',
            name='course',
            field=models.ForeignKey(
                help_text='Choose from the predefined list of courses.',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='students',
                to='practice.course',
            ),
        ),
    ]
