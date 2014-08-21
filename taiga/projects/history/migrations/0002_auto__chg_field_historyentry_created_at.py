# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'HistoryEntry.created_at'
        db.alter_column('history_historyentry', 'created_at', self.gf('django.db.models.fields.DateTimeField')())

    def backwards(self, orm):

        # Changing field 'HistoryEntry.created_at'
        db.alter_column('history_historyentry', 'created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    models = {
        'history.historyentry': {
            'Meta': {'ordering': "['created_at']", 'object_name': 'HistoryEntry'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'comment_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'diff': ('django_pgjson.fields.JsonField', [], {'default': 'None', 'blank': 'False'}),
            'id': ('django.db.models.fields.CharField', [], {'primary_key': 'True', 'default': "'9571feee-2ebf-11e4-8a54-1c75086d5bff'", 'unique': 'True', 'max_length': '255'}),
            'is_snapshot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'default': 'None', 'null': 'True', 'blank': 'True'}),
            'snapshot': ('django_pgjson.fields.JsonField', [], {'default': 'None', 'blank': 'False'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django_pgjson.fields.JsonField', [], {'default': 'None'}),
            'values': ('django_pgjson.fields.JsonField', [], {'default': 'None', 'blank': 'False'})
        }
    }

    complete_apps = ['history']