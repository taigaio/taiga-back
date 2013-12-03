# -*- coding: utf-8 -*-

# Patch api view for correctly return 401 responses on
# request is authenticated instead of 403
from . import monkey
monkey.patch_api_view()
monkey.patch_serializer()
monkey.patch_import_module()
monkey.patch_south_hacks()
