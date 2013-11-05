# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Project.default_points'
        db.add_column('projects_project', 'default_points',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.Points'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)

        # Adding field 'Project.default_us_status'
        db.add_column('projects_project', 'default_us_status',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.UserStoryStatus'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)

        # Adding field 'Project.default_task_status'
        db.add_column('projects_project', 'default_task_status',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.TaskStatus'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)

        # Adding field 'Project.default_priority'
        db.add_column('projects_project', 'default_priority',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.Priority'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)

        # Adding field 'Project.default_severity'
        db.add_column('projects_project', 'default_severity',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.Severity'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)

        # Adding field 'Project.default_issue_status'
        db.add_column('projects_project', 'default_issue_status',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.IssueStatus'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)

        # Adding field 'Project.default_issue_type'
        db.add_column('projects_project', 'default_issue_type',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.IssueType'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)

        # Adding field 'Project.default_question_status'
        db.add_column('projects_project', 'default_question_status',
                      self.gf('django.db.models.fields.related.OneToOneField')(null=True, to=orm['projects.QuestionStatus'], unique=True, related_name='+', on_delete=models.PROTECT, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Project.default_points'
        db.delete_column('projects_project', 'default_points_id')

        # Deleting field 'Project.default_us_status'
        db.delete_column('projects_project', 'default_us_status_id')

        # Deleting field 'Project.default_task_status'
        db.delete_column('projects_project', 'default_task_status_id')

        # Deleting field 'Project.default_priority'
        db.delete_column('projects_project', 'default_priority_id')

        # Deleting field 'Project.default_severity'
        db.delete_column('projects_project', 'default_severity_id')

        # Deleting field 'Project.default_issue_status'
        db.delete_column('projects_project', 'default_issue_status_id')

        # Deleting field 'Project.default_issue_type'
        db.delete_column('projects_project', 'default_issue_type_id')

        # Deleting field 'Project.default_question_status'
        db.delete_column('projects_project', 'default_question_status_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'projects.attachment': {
            'Meta': {'object_name': 'Attachment', 'ordering': "['project', 'created_date']"},
            'attached_file': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'max_length': '500', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'change_attachments'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'attachments'"})
        },
        'projects.issuestatus': {
            'Meta': {'object_name': 'IssueStatus', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_statuses'"})
        },
        'projects.issuetype': {
            'Meta': {'object_name': 'IssueType', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_types'"})
        },
        'projects.membership': {
            'Meta': {'object_name': 'Membership', 'ordering': "['project', 'role', 'user']", 'unique_together': "(('user', 'project'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'memberships'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'memberships'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'memberships'"})
        },
        'projects.points': {
            'Meta': {'object_name': 'Points', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'points'"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None', 'blank': 'True'})
        },
        'projects.priority': {
            'Meta': {'object_name': 'Priority', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'priorities'"})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['name']"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.IssueStatus']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.IssueType']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.Points']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.Priority']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.QuestionStatus']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.Severity']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.TaskStatus']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'null': 'True', 'to': "orm['projects.UserStoryStatus']", 'unique': 'True', 'related_name': "'+'", 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'through': "orm['projects.Membership']", 'to': "orm['users.User']", 'symmetrical': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'owned_projects'"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'unique': 'True', 'max_length': '250'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'default': '0', 'blank': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'})
        },
        'projects.questionstatus': {
            'Meta': {'object_name': 'QuestionStatus', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'question_status'"})
        },
        'projects.severity': {
            'Meta': {'object_name': 'Severity', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'severities'"})
        },
        'projects.taskstatus': {
            'Meta': {'object_name': 'TaskStatus', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'task_statuses'"})
        },
        'projects.userstorystatus': {
            'Meta': {'object_name': 'UserStoryStatus', 'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'us_statuses'"})
        },
        'users.role': {
            'Meta': {'object_name': 'Role', 'ordering': "['order', 'slug']"},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'blank': 'True', 'unique': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '9', 'default': "'#669933'"}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'max_length': '32', 'default': "'all_owned_projects'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'max_length': '500', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200', 'default': 'None', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['projects']