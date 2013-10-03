# -*- coding: utf-8 -*-

import json
import reversion

from rest_framework import serializers

from ..userstories.serializers import UserStorySerializer
from . import models



class MilestoneSerializer(serializers.ModelSerializer):
    user_stories = UserStorySerializer(many=True, required=False)

    class Meta:
        model = models.Milestone
