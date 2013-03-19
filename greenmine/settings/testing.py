# -*- coding: utf-8 -*-

from .development import *

GREENQUEUE_BACKEND = 'greenqueue.backends.sync.SyncService'
GREENQUEUE_WORKER_MANAGER = 'greenqueue.worker.sync.SyncManager'

INSTALLED_APPS.append('greenmine.taggit.tests')
