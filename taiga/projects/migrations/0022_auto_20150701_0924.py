# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0021_auto_20150504_1524'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projecttemplate',
            old_name='videoconferences_salt',
            new_name='videoconferences_extra_data',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='videoconferences_salt',
            new_name='videoconferences_extra_data',
        ),
        migrations.AlterField(
            model_name='project',
            name='videoconferences',
            field=models.CharField(blank=True, verbose_name='videoconference system', choices=[('appear-in', 'AppearIn'), ('jitsi', 'Jitsi'), ('custom', 'Custom'), ('talky', 'Talky')], null=True, max_length=250),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='projecttemplate',
            name='videoconferences',
            field=models.CharField(blank=True, verbose_name='videoconference system', choices=[('appear-in', 'AppearIn'), ('jitsi', 'Jitsi'), ('custom', 'Custom'), ('talky', 'Talky')], null=True, max_length=250),
            preserve_default=True,
        ),
    ]
