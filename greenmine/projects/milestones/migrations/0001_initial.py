# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Milestone'
        db.create_table('milestones_milestone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(blank=True, unique=True, max_length=40)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(blank=True, unique=True, max_length=250)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['users.User'], related_name='owned_milestones', null=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='milestones', to=orm['projects.Project'])),
            ('estimated_start', self.gf('django.db.models.fields.DateField')(blank=True, default=None, null=True)),
            ('estimated_finish', self.gf('django.db.models.fields.DateField')(blank=True, default=None, null=True)),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now_add=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('disponibility', self.gf('django.db.models.fields.FloatField')(blank=True, default=0.0, null=True)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal('milestones', ['Milestone'])

        # Adding unique constraint on 'Milestone', fields ['name', 'project']
        db.create_unique('milestones_milestone', ['name', 'project_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Milestone', fields ['name', 'project']
        db.delete_unique('milestones_milestone', ['name', 'project_id'])

        # Deleting model 'Milestone'
        db.delete_table('milestones_milestone')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'milestones.milestone': {
            'Meta': {'object_name': 'Milestone', 'unique_together': "(('name', 'project'),)", 'ordering': "['project', '-created_date']"},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'disponibility': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': '0.0', 'null': 'True'}),
            'estimated_finish': ('django.db.models.fields.DateField', [], {'blank': 'True', 'default': 'None', 'null': 'True'}),
            'estimated_start': ('django.db.models.fields.DateField', [], {'blank': 'True', 'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'related_name': "'owned_milestones'", 'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'milestones'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'unique': 'True', 'max_length': '250'}),
            'uuid': ('django.db.models.fields.CharField', [], {'blank': 'True', 'unique': 'True', 'max_length': '40'})
        },
        'projects.membership': {
            'Meta': {'object_name': 'Membership', 'unique_together': "(('user', 'project'),)", 'ordering': "['project', 'role', 'user']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.User']"})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['name']"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'through': "orm['projects.Membership']", 'to': "orm['users.User']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'unique': 'True', 'max_length': '250'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': '0', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'blank': 'True', 'unique': 'True', 'max_length': '40'})
        },
        'users.role': {
            'Meta': {'object_name': 'Role', 'ordering': "['order', 'slug']"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'unique': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'#669933'", 'max_length': '9'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "''", 'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'symmetrical': 'False', 'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'null': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': 'None', 'null': 'True', 'max_length': '200'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['milestones']