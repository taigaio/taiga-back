# -*- coding: utf-8 -*-
from django.contrib import admin

from greenmine.questions.models import Question, QuestionStatus

import reversion


class QuestionAdmin(reversion.VersionAdmin):
    list_display = ["subject", "project", "owner"]

admin.site.register(Question, QuestionAdmin)


class QuestionStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

admin.site.register(QuestionStatus, QuestionStatusAdmin)
