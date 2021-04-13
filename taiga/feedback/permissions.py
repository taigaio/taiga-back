# -*- coding: utf-8 -*-
from taiga.base.api.permissions import TaigaResourcePermission
from taiga.base.api.permissions import IsAuthenticated


class FeedbackPermission(TaigaResourcePermission):
    create_perms = IsAuthenticated()
