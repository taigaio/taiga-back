# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0020_membership_user_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='create at'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='project',
            name='videoconferences',
            field=models.CharField(max_length=250, blank=True, choices=[('appear-in', 'AppearIn'), ('jitsi', 'Jitsi'), ('talky', 'Talky')], null=True, verbose_name='videoconference system'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='projecttemplate',
            name='videoconferences',
            field=models.CharField(max_length=250, blank=True, choices=[('appear-in', 'AppearIn'), ('jitsi', 'Jitsi'), ('talky', 'Talky')], null=True, verbose_name='videoconference system'),
            preserve_default=True,
        ),
    ]
