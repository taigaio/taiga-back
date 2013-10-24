# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Task'
        db.create_table('tasks_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, blank=True, max_length=40)),
            ('user_story', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', to=orm['userstories.UserStory'], null=True, blank=True)),
            ('ref', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True, db_index=True, default=None)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='owned_tasks', to=orm['users.User'], null=True, blank=True, default=None)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', to=orm['projects.TaskStatus'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', to=orm['projects.Project'])),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', to=orm['milestones.Milestone'], null=True, blank=True, default=None)),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('finished_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('assigned_to', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_storys_assigned_to_me', to=orm['users.User'], null=True, blank=True, default=None)),
            ('tags', self.gf('picklefield.fields.PickledObjectField')(blank=True)),
            ('is_iocaine', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('tasks', ['Task'])

        # Adding unique constraint on 'Task', fields ['ref', 'project']
        db.create_unique('tasks_task', ['ref', 'project_id'])

        # Adding M2M table for field watchers on 'Task'
        m2m_table_name = db.shorten_name('tasks_task_watchers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('task', models.ForeignKey(orm['tasks.task'], null=False)),
            ('user', models.ForeignKey(orm['users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['task_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Task', fields ['ref', 'project']
        db.delete_unique('tasks_task', ['ref', 'project_id'])

        # Deleting model 'Task'
        db.delete_table('tasks_task')

        # Removing M2M table for field watchers on 'Task'
        db.delete_table(db.shorten_name('tasks_task_watchers'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'milestones.milestone': {
            'Meta': {'ordering': "['project', '-created_date']", 'unique_together': "(('name', 'project'),)", 'object_name': 'Milestone'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disponibility': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True', 'default': '0.0'}),
            'estimated_finish': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True', 'default': 'None'}),
            'estimated_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True', 'default': 'None'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_milestones'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'milestones'", 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'blank': 'True', 'max_length': '40'})
        },
        'projects.membership': {
            'Meta': {'ordering': "['project', 'role', 'user']", 'unique_together': "(('user', 'project'),)", 'object_name': 'Membership'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['projects.Project']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.Role']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': "orm['users.User']"})
        },
        'projects.points': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'Points'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'points'", 'to': "orm['projects.Project']"}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True', 'default': 'None'})
        },
        'projects.project': {
            'Meta': {'ordering': "['name']", 'object_name': 'Project'},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_issue_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_task_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'last_us_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'default': '1'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'through': "orm['projects.Membership']", 'to': "orm['users.User']", 'symmetrical': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_projects'", 'to': "orm['users.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'total_milestones': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True', 'default': '0'}),
            'total_story_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'default': 'None'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'blank': 'True', 'max_length': '40'})
        },
        'projects.taskstatus': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'TaskStatus'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'default': "'#999999'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'task_statuses'", 'to': "orm['projects.Project']"})
        },
        'projects.userstorystatus': {
            'Meta': {'ordering': "['project', 'name']", 'unique_together': "(('project', 'name'),)", 'object_name': 'UserStoryStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_statuses'", 'to': "orm['projects.Project']"})
        },
        'tasks.task': {
            'Meta': {'ordering': "['project', 'created_date']", 'unique_together': "(('ref', 'project'),)", 'object_name': 'Task'},
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_storys_assigned_to_me'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True', 'default': 'None'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'finished_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_iocaine': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['milestones.Milestone']", 'null': 'True', 'blank': 'True', 'default': 'None'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_tasks'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True', 'default': 'None'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['projects.Project']"}),
            'ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True', 'db_index': 'True', 'default': 'None'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['projects.TaskStatus']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'user_story': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['userstories.UserStory']", 'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'blank': 'True', 'max_length': '40'}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'watched_tasks'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True', 'symmetrical': 'False'})
        },
        'users.role': {
            'Meta': {'ordering': "['order', 'slug']", 'object_name': 'Role'},
            'computable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'blank': 'True', 'max_length': '250'})
        },
        'users.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'color': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '9', 'default': "'#669933'"}),
            'colorize_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_language': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'default_timezone': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20', 'default': "''"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'photo': ('django.db.models.fields.files.FileField', [], {'null': 'True', 'blank': 'True', 'max_length': '500'}),
            'token': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '200', 'default': 'None'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'userstories.rolepoints': {
            'Meta': {'object_name': 'RolePoints', 'unique_together': "(('user_story', 'role'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['projects.Points']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['users.Role']"}),
            'user_story': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_points'", 'to': "orm['userstories.UserStory']"})
        },
        'userstories.userstory': {
            'Meta': {'ordering': "['project', 'order']", 'unique_together': "(('ref', 'project'),)", 'object_name': 'UserStory'},
            'client_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'finish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'related_name': "'user_stories'", 'to': "orm['milestones.Milestone']", 'on_delete': 'models.SET_NULL', 'default': 'None'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_user_stories'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'points': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'userstories'", 'through': "orm['userstories.RolePoints']", 'to': "orm['projects.Points']", 'symmetrical': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'to': "orm['projects.Project']"}),
            'ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True', 'db_index': 'True', 'default': 'None'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_stories'", 'to': "orm['projects.UserStoryStatus']", 'null': 'True', 'blank': 'True', 'on_delete': 'models.SET_NULL'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'tags': ('picklefield.fields.PickledObjectField', [], {'blank': 'True'}),
            'team_requirement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'blank': 'True', 'max_length': '40'}),
            'watchers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'watched_us'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True', 'symmetrical': 'False'})
        }
    }

    complete_apps = ['tasks']