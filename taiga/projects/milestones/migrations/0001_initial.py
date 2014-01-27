# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Milestone'
        db.create_table('milestones_milestone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=250, unique=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(null=True, related_name='owned_milestones', blank=True, to=orm['users.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='milestones', to=orm['projects.Project'])),
            ('estimated_start', self.gf('django.db.models.fields.DateField')(null=True, default=None, blank=True)),
            ('estimated_finish', self.gf('django.db.models.fields.DateField')(null=True, default=None, blank=True)),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('disponibility', self.gf('django.db.models.fields.FloatField')(null=True, default=0.0, blank=True)),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'domains.domain': {
            'Meta': {'object_name': 'Domain', 'ordering': "('domain',)"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheme': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '60', 'default': 'None'})
        },
        'milestones.milestone': {
            'Meta': {'object_name': 'Milestone', 'unique_together': "(('name', 'project'),)", 'ordering': "['project', 'created_date']"},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disponibility': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': '0.0', 'blank': 'True'}),
            'estimated_finish': ('django.db.models.fields.DateField', [], {'null': 'True', 'default': 'None', 'blank': 'True'}),
            'estimated_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'default': 'None', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'owned_milestones'", 'blank': 'True', 'to': "orm['users.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'milestones'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'})
        },
        'projects.issuestatus': {
            'Meta': {'object_name': 'IssueStatus', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.issuetype': {
            'Meta': {'object_name': 'IssueType', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_types'", 'to': "orm['projects.Project']"})
        },
        'projects.membership': {
            'Meta': {'object_name': 'Membership', 'ordering': "['project', 'role']"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'default': 'datetime.datetime.now', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'max_length': '255', 'default': 'None'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '60', 'unique': 'True', 'default': 'None', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'memberships'", 'default': 'None', 'blank': 'True', 'to': "orm['users.User']"})
        },
        'projects.points': {
            'Meta': {'object_name': 'Points', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None', 'blank': 'True'})
        },
        'projects.priority': {
            'Meta': {'object_name': 'Priority', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'priorities'", 'to': "orm['projects.Project']"})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['name']"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.IssueStatus']"}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.IssueType']"}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.Points']"}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.Priority']"}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.QuestionStatus']"}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.Severity']"}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.TaskStatus']"}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'related_name': "'+'", 'to': "orm['projects.UserStoryStatus']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'to': "orm['users.User']", 'through': "orm['projects.Membership']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'projects'", 'default': 'None', 'to': "orm['domains.Domain']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'default': '0', 'blank': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'})
        },
        'projects.questionstatus': {
            'Meta': {'object_name': 'QuestionStatus', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_status'", 'to': "orm['projects.Project']"})
        },
        'projects.severity': {
            'Meta': {'object_name': 'Severity', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'severities'", 'to': "orm['projects.Project']"})
        },
        'projects.taskstatus': {
            'Meta': {'object_name': 'TaskStatus', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'object_name': 'UserStoryStatus', 'unique_together': "(('project', 'name'),)", 'ordering': "['project', 'order', 'name']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_statuses'", 'to': "orm['projects.Project']"})
        },
        'users.role': {
            'Meta': {'object_name': 'Role', 'ordering': "['order', 'slug']"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'roles'", 'to': "orm['auth.Permission']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '9', 'default': "'#669933'", 'blank': 'True'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "''", 'blank': 'True'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "''", 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'", 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'max_length': '32', 'default': "'all_owned_projects'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'max_length': '500', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200', 'default': 'None', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'", 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['milestones']