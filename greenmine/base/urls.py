# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from greenmine.base import api, routers

router = routers.Router(trailing_slash=False)
router.register("users", api.UsersViewSet, base_name="users")
router.register("roles", api.RolesViewSet, base_name="roles")
router.register("search", api.Search, base_name="search")

urlpatterns = router.urls

