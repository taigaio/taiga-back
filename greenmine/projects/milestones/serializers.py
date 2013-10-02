# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.projects.userstories.serializers import user_stories

from . import models

import json, reversion


class MilestoneSerializer(serializers.ModelSerializer):
    user_stories = UserStorySerializer(many=True, required=False)

    class Meta:
        model = models.Milestone
