# Generated manually for the Student model enhancements
# (timestamps, validators, ordering, related_name)

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('practice', '0002_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='student',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='age',
            field=models.PositiveIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(120),
                ]
            ),
        ),
        migrations.AlterField(
            model_name='student',
            name='phone',
            field=models.CharField(
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Enter a valid phone number (7-15 digits, optionally starting with '+').",
                        regex='^\\+?\\d{7,15}$',
                    )
                ],
            ),
        ),
        migrations.AlterModelOptions(
            name='student',
            options={'ordering': ['-created_at'], 'verbose_name': 'Student', 'verbose_name_plural': 'Students'},
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='profile',
                to='auth.user',
            ),
        ),
    ]
