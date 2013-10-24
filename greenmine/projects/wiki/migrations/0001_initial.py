# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WikiPage'
        db.create_table('wiki_wikipage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='wiki_pages')),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=500)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, related_name='owned_wiki_pages', blank=True)),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now_add=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now=True)),
        ))
        db.send_create_signal('wiki', ['WikiPage'])

        # Adding unique constraint on 'WikiPage', fields ['project', 'slug']
        db.create_unique('wiki_wikipage', ['project_id', 'slug'])

        # Adding M2M table for field watchers on 'WikiPage'
        m2m_table_name = db.shorten_name('wiki_wikipage_watchers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('wikipage', models.ForeignKey(orm['wiki.wikipage'], null=False)),
            ('user', models.ForeignKey(orm['users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['wikipage_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'WikiPage', fields ['project', 'slug']
        db.delete_unique('wiki_wikipage', ['project_id', 'slug'])

        # Deleting model 'WikiPage'
        db.delete_table('wiki_wikipage')

        # Removing M2M table for field watchers on 'WikiPage'
        db.delete_table(db.shorten_name('wiki_wikipage_watchers'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role', 'user']", 'object_name': 'Membership', 'unique_together': "(('user', 'project'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'memberships'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'memberships'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'memberships'"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['users.User']", 'symmetrical': 'False', 'related_name': "'projects'", 'through': "orm['projects.Membership']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'owned_projects'"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': '0', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '40', 'unique': 'True'})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role'},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'related_name': "'roles'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'max_length': '250', 'unique': 'True'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'#669933'", 'max_length': '9'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'max_length': '500', 'null': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': 'None', 'max_length': '200', 'null': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'wiki.wikipage': {
            'Meta': {'ordering': "['project', 'slug']", 'object_name': 'WikiPage', 'unique_together': "(('project', 'slug'),)"},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'related_name': "'owned_wiki_pages'", 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'wiki_pages'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '500'}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['users.User']", 'symmetrical': 'False', 'related_name': "'watched_wiki_pages'", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['wiki']