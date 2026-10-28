from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    """Ensure every User always has an associated Profile.

    - On first creation: create the Profile. Superusers (e.g. accounts made
      with `createsuperuser`) automatically get the "admin" role; everyone
      else defaults to "student" (set explicitly at registration time via
      RegisterForm for self-registered accounts).
    - On subsequent saves: nothing further to do, since Profile fields
      (role, profile_picture, bio) are edited directly via their own forms
      and don't need to be re-derived whenever the User model changes.
    """

    if created:
        role = Profile.ROLE_ADMIN if instance.is_superuser else Profile.ROLE_STUDENT
        Profile.objects.get_or_create(user=instance, defaults={"role": role})
