from django.db import migrations, models


PREDEFINED_COURSES = [
    ("B.Tech Computer Science", "BTCS"),
    ("B.Tech Information Technology", "BTIT"),
    ("B.Tech Electronics & Communication", "BTEC"),
    ("B.Tech Mechanical Engineering", "BTME"),
    ("B.Tech Civil Engineering", "BTCE"),
    ("BCA - Bachelor of Computer Applications", "BCA"),
    ("MCA - Master of Computer Applications", "MCA"),
    ("B.Sc Mathematics", "BSCM"),
    ("B.Com", "BCOM"),
    ("MBA - Master of Business Administration", "MBA"),
    ("Artificial Intelligence & Machine Learning", "AIML"),
]


def seed_predefined_courses(apps, schema_editor):
    Course = apps.get_model("practice", "Course")

    for name, code in PREDEFINED_COURSES:
        Course.objects.get_or_create(name=name, defaults={"code": code})


def remove_predefined_courses(apps, schema_editor):
    Course = apps.get_model("practice", "Course")
    names = [name for name, _ in PREDEFINED_COURSES]
    Course.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('practice', '0005_backfill_admin_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
                ('code', models.CharField(blank=True, help_text="Optional short code, e.g. 'CSE101'.", max_length=20, null=True, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(seed_predefined_courses, remove_predefined_courses),
    ]
