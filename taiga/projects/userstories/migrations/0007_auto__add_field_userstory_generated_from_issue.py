# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserStory.generated_from_issue'
        db.add_column('userstories_userstory', 'generated_from_issue',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='generated_user_stories', null=True, to=orm['issues.Issue'], blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'UserStory.generated_from_issue'
        db.delete_column('userstories_userstory', 'generated_from_issue_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'domains.domain': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Domain'},
            'alias_of': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'+'", 'null': 'True', 'to': "orm['domains.Domain']", 'blank': 'True'}),
            'default_language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheme': ('django.db.models.fields.CharField', [], {'default': 'None', 'null': 'True', 'max_length': '60'})
        },
        'issues.issue': {
            'Meta': {'ordering': "['project', 'created_date']", 'unique_together': "(('ref', 'project'),)", 'object_name': 'Issue'},
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'issues_assigned_to_me'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'blocked_note': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'finished_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'issues'", 'null': 'True', 'to': "orm['milestones.Milestone']", 'blank': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'owned_issues'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'priority': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': "orm['projects.Priority']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': "orm['projects.Project']"}),
            'ref': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'severity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': "orm['projects.Severity']"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': "orm['projects.IssueStatus']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': "orm['projects.IssueType']"}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'watched_issues'", 'symmetrical': 'False', 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'})
        },
        'milestones.milestone': {
            'Meta': {'ordering': "['project', 'created_date']", 'unique_together': "(('name', 'project'),)", 'object_name': 'Milestone'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disponibility': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True', 'blank': 'True'}),
            'estimated_finish': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'estimated_start': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_milestones'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'milestones'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'})
        },
        'projects.issuestatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'IssueStatus'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.issuetype': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'IssueType'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue_types'", 'to': "orm['projects.Project']"})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role']", 'object_name': 'Membership'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'null': 'True', 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'token': ('django.db.models.fields.CharField', [], {'default': 'None', 'null': 'True', 'max_length': '60', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'memberships'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Points'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'projects.priority': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Priority'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'priorities'", 'to': "orm['projects.Project']"})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.IssueStatus']", 'null': 'True'}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.IssueType']", 'null': 'True'}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.Points']", 'null': 'True'}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.Priority']", 'null': 'True'}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.QuestionStatus']", 'null': 'True'}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.Severity']", 'null': 'True'}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.TaskStatus']", 'null': 'True'}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'blank': 'True', 'unique': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['projects.UserStoryStatus']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projects'", 'null': 'True', 'to': "orm['domains.Domain']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_backlog_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_issues_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_kanban_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wiki_activated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '0', 'null': 'True'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '0', 'null': 'True'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '0', 'null': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'through': "orm['projects.Membership']", 'to': "orm['users.User']", 'symmetrical': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'unique': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'unique': 'True', 'blank': 'True'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            'videoconferences': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '250', 'blank': 'True'}),
            'videoconferences_salt': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '250', 'blank': 'True'})
        },
        'projects.questionstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'QuestionStatus'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_status'", 'to': "orm['projects.Project']"})
        },
        'projects.severity': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Severity'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'severities'", 'to': "orm['projects.Project']"})
        },
        'projects.taskstatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'TaskStatus'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'order', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_statuses'", 'to': "orm['projects.Project']"})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'unique_together': "(('slug', 'project'),)", 'object_name': 'Role'},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'roles'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#72bd35'", 'max_length': '9', 'blank': 'True'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'symmetrical': 'False', 'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'default': "'all_owned_projects'", 'max_length': '32'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'max_length': '500', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'default': 'None', 'null': 'True', 'max_length': '200', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'userstories.rolepoints': {
            'Meta': {'ordering': "['user_story', 'role']", 'unique_together': "(('user_story', 'role'),)", 'object_name': 'RolePoints'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['projects.Points']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['users.Role']"}),
            'user_story': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['userstories.UserStory']"})
        },
        'userstories.userstory': {
            'Meta': {'ordering': "['project', 'order', 'ref']", 'unique_together': "(('ref', 'project'),)", 'object_name': 'UserStory'},
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'userstories_assigned_to_me'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'blocked_note': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'client_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'finish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'generated_from_issue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'generated_user_stories'", 'null': 'True', 'to': "orm['issues.Issue']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['milestones.Milestone']", 'default': 'None', 'null': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_user_stories'", 'null': 'True', 'to': "orm['users.User']", 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'points': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'userstories'", 'through': "orm['userstories.RolePoints']", 'to': "orm['projects.Points']", 'symmetrical': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'to': "orm['projects.Project']"}),
            'ref': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'null': 'True', 'to': "orm['projects.UserStoryStatus']", 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'team_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'watched_user_stories'", 'symmetrical': 'False', 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'})
        }
    }

    complete_apps = ['userstories']