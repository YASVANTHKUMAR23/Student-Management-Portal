from django.db import migrations


def set_admin_role_for_superusers(apps, schema_editor):
    """The 'role' field was added with a blanket default of 'student' for
    every existing Profile row (since Django can't know a person's
    intended role in advance). This backfills the correct 'admin' role
    for any account that's already a Django superuser, so an existing
    admin isn't accidentally demoted to 'student' after this migration."""

    Profile = apps.get_model("practice", "Profile")

    Profile.objects.filter(user__is_superuser=True).update(role="admin")


def reverse_noop(apps, schema_editor):
    # Nothing sensible to reverse to — leave roles as they are.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('practice', '0004_profile_role_student_linked_user'),
    ]

    operations = [
        migrations.RunPython(set_admin_role_for_superusers, reverse_noop),
    ]
