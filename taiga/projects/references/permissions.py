# -*- coding: utf-8 -*-
from taiga.base.api.permissions import (TaigaResourcePermission, HasProjectPerm,
                                        IsProjectAdmin, AllowAny)


class ResolverPermission(TaigaResourcePermission):
    list_perms = HasProjectPerm('view_project')
