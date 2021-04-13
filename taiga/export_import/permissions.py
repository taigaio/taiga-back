# -*- coding: utf-8 -*-
from taiga.base.api.permissions import (TaigaResourcePermission,
                                        IsProjectAdmin, IsAuthenticated)


class ImportExportPermission(TaigaResourcePermission):
    import_project_perms = IsAuthenticated()
    import_item_perms = IsProjectAdmin()
    export_project_perms = IsProjectAdmin()
    load_dump_perms = IsAuthenticated()
