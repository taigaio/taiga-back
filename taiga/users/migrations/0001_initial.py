# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import django.utils.timezone
import re
import django.core.validators
import taiga.users.models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(max_length=30, help_text='Required. 30 characters or fewer. Letters, numbers and /./-/_ characters', verbose_name='username', unique=True, validators=[django.core.validators.RegexValidator(re.compile('^[\\w.-]+$', 32), 'Enter a valid username.', 'invalid')])),
                ('email', models.EmailField(max_length=75, blank=True, verbose_name='email address')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('full_name', models.CharField(max_length=256, blank=True, verbose_name='full name')),
                ('color', models.CharField(default=taiga.users.models.generate_random_hex_color, max_length=9, blank=True, verbose_name='color')),
                ('bio', models.TextField(default='', blank=True, verbose_name='biography')),
                ('photo', models.FileField(null=True, max_length=500, blank=True, verbose_name='photo', upload_to='users/photo')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('default_language', models.CharField(default='', max_length=20, blank=True, verbose_name='default language')),
                ('default_timezone', models.CharField(default='', max_length=20, blank=True, verbose_name='default timezone')),
                ('colorize_tags', models.BooleanField(default=False, verbose_name='colorize tags')),
                ('token', models.CharField(default=None, max_length=200, blank=True, verbose_name='token', null=True)),
                ('email_token', models.CharField(default=None, max_length=200, blank=True, verbose_name='email token', null=True)),
                ('new_email', models.EmailField(null=True, max_length=75, blank=True, verbose_name='new email address')),
                ('github_id', models.IntegerField(null=True, blank=True, verbose_name='github ID')),
            ],
            options={
                'verbose_name_plural': 'users',
                'permissions': (('view_user', 'Can view user'),),
                'verbose_name': 'user',
                'ordering': ['username'],
            },
            bases=(models.Model,),
        ),
    ]
