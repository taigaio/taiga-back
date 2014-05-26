# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Timeline'
        db.create_table('timeline_timeline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('namespace', self.gf('django.db.models.fields.SlugField')(default='default', max_length=50)),
            ('event_type', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('data', self.gf('django_pgjson.fields.JsonField')(null=False, blank=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('timeline', ['Timeline'])

        # Adding index on 'Timeline', fields ['content_type', 'object_id', 'namespace']
        db.create_index('timeline_timeline', ['content_type_id', 'object_id', 'namespace'])


    def backwards(self, orm):
        # Removing index on 'Timeline', fields ['content_type', 'object_id', 'namespace']
        db.delete_index('timeline_timeline', ['content_type_id', 'object_id', 'namespace'])

        # Deleting model 'Timeline'
        db.delete_table('timeline_timeline')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'db_table': "'django_content_type'", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'timeline.timeline': {
            'Meta': {'object_name': 'Timeline', 'index_together': "[('content_type', 'object_id', 'namespace')]"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django_pgjson.fields.JsonField', [], {'null': 'False', 'blank': 'False'}),
            'event_type': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namespace': ('django.db.models.fields.SlugField', [], {'default': "'default'", 'max_length': '50'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['timeline']