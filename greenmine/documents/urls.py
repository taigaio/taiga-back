# -*- coding: utf-8 -*-

from greenmine.base import routers

from . import api


router = routers.SimpleRouter(trailing_slash=False)
router.register(r"documents", api.DocumentsViewSet, base_name="documents")

urlpatterns = router.urls
