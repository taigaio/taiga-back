# -*- coding: utf-8 -*-
from django.contrib import admin

from greenmine.questions.models import Question, QuestionResponse


class QuestionAdmin(admin.ModelAdmin):
    list_display = ["subject", "project", "owner"]

admin.site.register(Question, QuestionAdmin)


class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "owner"]

admin.site.register(QuestionResponse, QuestionResponseAdmin)
