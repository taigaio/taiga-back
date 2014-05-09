# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HistoryEntry'
        db.create_table('history_historyentry', (
            ('id', self.gf('django.db.models.fields.CharField')(unique=True, default='e3cec230-d752-11e3-a409-b499ba5650c0', max_length=255, primary_key=True)),
            ('user', self.gf('django_pgjson.fields.JsonField')(default=None)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now_add=True)),
            ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('is_snapshot', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('key', self.gf('django.db.models.fields.CharField')(blank=True, null=True, default=None, max_length=255)),
            ('diff', self.gf('django_pgjson.fields.JsonField')(blank=False, default=None)),
            ('snapshot', self.gf('django_pgjson.fields.JsonField')(blank=False, default=None)),
            ('values', self.gf('django_pgjson.fields.JsonField')(blank=False, default=None)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('comment_html', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('history', ['HistoryEntry'])


    def backwards(self, orm):
        # Deleting model 'HistoryEntry'
        db.delete_table('history_historyentry')


    models = {
        'history.historyentry': {
            'Meta': {'object_name': 'HistoryEntry', 'ordering': "['created_at']"},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'comment_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'diff': ('django_pgjson.fields.JsonField', [], {'blank': 'False', 'default': 'None'}),
            'id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'default': "'e3cf38a0-d752-11e3-a409-b499ba5650c0'", 'max_length': '255', 'primary_key': 'True'}),
            'is_snapshot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'default': 'None', 'max_length': '255'}),
            'snapshot': ('django_pgjson.fields.JsonField', [], {'blank': 'False', 'default': 'None'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django_pgjson.fields.JsonField', [], {'default': 'None'}),
            'values': ('django_pgjson.fields.JsonField', [], {'blank': 'False', 'default': 'None'})
        }
    }

    complete_apps = ['history']