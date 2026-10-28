import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('practice', '0007_student_course_fk'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='teacher',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='taught_students',
                to=settings.AUTH_USER_MODEL,
                help_text='The teacher assigned to this student.',
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='courses',
            field=models.ManyToManyField(
                blank=True,
                related_name='teachers',
                to='practice.course',
                help_text='Courses this teacher is assigned to (Teacher accounts only).',
            ),
        ),
    ]
