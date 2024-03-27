# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
