# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20140903_0920'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WikiLink',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=500)),
                ('href', models.SlugField(max_length=500, verbose_name='href')),
                ('order', models.PositiveSmallIntegerField(default=1, verbose_name='order')),
                ('project', models.ForeignKey(verbose_name='project', related_name='wiki_links', to='projects.Project', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['project', 'order'],
                'verbose_name_plural': 'wiki links',
                'verbose_name': 'wiki link',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WikiPage',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('version', models.IntegerField(default=1, verbose_name='version')),
                ('slug', models.SlugField(max_length=500, verbose_name='slug')),
                ('content', models.TextField(blank=True, verbose_name='content')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('last_modifier', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='last modifier', related_name='last_modified_wiki_pages', blank=True, on_delete=models.SET_NULL)),
                ('owner', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='owner', related_name='owned_wiki_pages', blank=True, on_delete=models.SET_NULL)),
                ('project', models.ForeignKey(verbose_name='project', related_name='wiki_pages', to='projects.Project', on_delete=models.CASCADE)),
                ('watchers', models.ManyToManyField(null=True, related_name='wiki_wikipage+', blank=True, verbose_name='watchers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['project', 'slug'],
                'verbose_name_plural': 'wiki pages',
                'verbose_name': 'wiki page',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='wikipage',
            unique_together=set([('project', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='wikilink',
            unique_together=set([('project', 'href')]),
        ),
    ]
