# Generated for instance-wide, nullable language and theme defaults.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_default_row(apps, schema_editor):
    apps.get_model("instance_settings", "InstanceDefaults").objects.create(pk=1)


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="InstanceDefaults",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("default_language", models.CharField(blank=True, default="", max_length=20)),
                ("default_theme", models.CharField(blank=True, default="", max_length=100)),
                ("revision", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="InstanceDefaultsAudit",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("old_language", models.CharField(blank=True, max_length=20)),
                ("new_language", models.CharField(blank=True, max_length=20)),
                ("old_theme", models.CharField(blank=True, max_length=100)),
                ("new_theme", models.CharField(blank=True, max_length=100)),
                ("revision", models.PositiveIntegerField()),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(seed_default_row, migrations.RunPython.noop),
    ]
