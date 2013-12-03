# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RolePoints'
        db.create_table('userstories_rolepoints', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_story', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['userstories.UserStory'], related_name='role_points')),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.Role'], related_name='role_points')),
            ('points', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Points'], related_name='role_points')),
        ))
        db.send_create_signal('userstories', ['RolePoints'])

        # Adding unique constraint on 'RolePoints', fields ['user_story', 'role']
        db.create_unique('userstories_rolepoints', ['user_story_id', 'role_id'])

        # Adding model 'UserStory'
        db.create_table('userstories_userstory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ref', self.gf('django.db.models.fields.BigIntegerField')(default=None, blank=True, db_index=True, null=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_stories', default=None, blank=True, on_delete=models.SET_NULL, null=True, to=orm['milestones.Milestone'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'], related_name='user_stories')),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='owned_user_stories', blank=True, on_delete=models.SET_NULL, null=True, to=orm['users.User'])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_stories', blank=True, on_delete=models.SET_NULL, null=True, to=orm['projects.UserStoryStatus'])),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=100)),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now_add=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now=True)),
            ('finish_date', self.gf('django.db.models.fields.DateTimeField')(blank=True, null=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('client_requirement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('team_requirement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('tags', self.gf('picklefield.fields.PickledObjectField')(blank=True)),
        ))
        db.send_create_signal('userstories', ['UserStory'])

        # Adding unique constraint on 'UserStory', fields ['ref', 'project']
        db.create_unique('userstories_userstory', ['ref', 'project_id'])

        # Adding M2M table for field watchers on 'UserStory'
        m2m_table_name = db.shorten_name('userstories_userstory_watchers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userstory', models.ForeignKey(orm['userstories.userstory'], null=False)),
            ('user', models.ForeignKey(orm['users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['userstory_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserStory', fields ['ref', 'project']
        db.delete_unique('userstories_userstory', ['ref', 'project_id'])

        # Removing unique constraint on 'RolePoints', fields ['user_story', 'role']
        db.delete_unique('userstories_rolepoints', ['user_story_id', 'role_id'])

        # Deleting model 'RolePoints'
        db.delete_table('userstories_rolepoints')

        # Deleting model 'UserStory'
        db.delete_table('userstories_userstory')

        # Removing M2M table for field watchers on 'UserStory'
        db.delete_table(db.shorten_name('userstories_userstory_watchers'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'", 'ordering': "('name',)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'domains.domain': {
            'Meta': {'object_name': 'Domain', 'ordering': "('domain',)"},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheme': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '60', 'null': 'True'})
        },
        'milestones.milestone': {
            'Meta': {'unique_together': "(('name', 'project'),)", 'object_name': 'Milestone', 'ordering': "['project', 'created_date']"},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'disponibility': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'blank': 'True', 'null': 'True'}),
            'estimated_finish': ('django.db.models.fields.DateField', [], {'default': 'None', 'blank': 'True', 'null': 'True'}),
            'estimated_start': ('django.db.models.fields.DateField', [], {'default': 'None', 'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_milestones'", 'blank': 'True', 'null': 'True', 'to': "orm['users.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'milestones'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'})
        },
        'projects.issuestatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'IssueStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_statuses'"})
        },
        'projects.issuetype': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'IssueType', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'issue_types'"})
        },
        'projects.membership': {
            'Meta': {'object_name': 'Membership', 'ordering': "['project', 'role']"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True', 'auto_now_add': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'memberships'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'memberships'"}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'default': 'None', 'blank': 'True', 'max_length': '60', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'default': 'None', 'blank': 'True', 'null': 'True', 'to': "orm['users.User']"})
        },
        'projects.points': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Points', 'ordering': "['project', 'order', 'name']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'points'"}),
            'value': ('django.db.models.fields.FloatField', [], {'default': 'None', 'blank': 'True', 'null': 'True'})
        },
        'projects.priority': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Priority', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'priorities'"})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['name']"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'default_issue_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.IssueStatus']"}),
            'default_issue_type': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.IssueType']"}),
            'default_points': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.Points']"}),
            'default_priority': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.Priority']"}),
            'default_question_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.QuestionStatus']"}),
            'default_severity': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.Severity']"}),
            'default_task_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.TaskStatus']"}),
            'default_us_status': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'related_name': "'+'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.UserStoryStatus']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'default': '1', 'null': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'to': "orm['users.User']", 'through': "orm['projects.Membership']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'related_name': "'owned_projects'"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['domains.Domain']", 'null': 'True', 'related_name': "'projects'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True', 'null': 'True'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'})
        },
        'projects.questionstatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'QuestionStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'question_status'"})
        },
        'projects.severity': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Severity', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'severities'"})
        },
        'projects.taskstatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'TaskStatus', 'ordering': "['project', 'order', 'name']"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#999999'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'task_statuses'"})
        },
        'projects.userstorystatus': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus', 'ordering': "['project', 'order', 'name']"},
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
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Permission']", 'related_name': "'roles'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'object_name': 'User', 'ordering': "['username']"},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#669933'", 'blank': 'True', 'max_length': '9'}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '20'}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'notify_changes_by_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_level': ('django.db.models.fields.CharField', [], {'default': "'all_owned_projects'", 'max_length': '32'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'default': 'None', 'blank': 'True', 'max_length': '200', 'null': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'userstories.rolepoints': {
            'Meta': {'unique_together': "(('user_story', 'role'),)", 'object_name': 'RolePoints', 'ordering': "['user_story', 'role']"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Points']", 'related_name': "'role_points'"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Role']", 'related_name': "'role_points'"}),
            'user_story': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['userstories.UserStory']", 'related_name': "'role_points'"})
        },
        'userstories.userstory': {
            'Meta': {'unique_together': "(('ref', 'project'),)", 'object_name': 'UserStory', 'ordering': "['project', 'order']"},
            'client_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'finish_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'default': 'None', 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['milestones.Milestone']"}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_user_stories'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['users.User']"}),
            'points': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'userstories'", 'to': "orm['projects.Points']", 'through': "orm['userstories.RolePoints']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'related_name': "'user_stories'"}),
            'ref': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'blank': 'True', 'db_index': 'True', 'null': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'blank': 'True', 'on_delete': 'models.SET_NULL', 'null': 'True', 'to': "orm['projects.UserStoryStatus']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'team_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'watched_us'", 'blank': 'True', 'null': 'True', 'to': "orm['users.User']"})
        }
    }

    complete_apps = ['userstories']