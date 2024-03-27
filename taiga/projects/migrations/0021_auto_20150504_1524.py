# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
