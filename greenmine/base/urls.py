# -*- coding: utf-8 -*-

from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers

from django.conf.urls import patterns, url
from greenmine.base import api

# Special router for actions.
actions_router = routers.Route(url=r'^{prefix}/actions/{methodname}{trailing_slash}$',
                               mapping={'{httpmethod}': '{methodname}'},
                               name='{basename}-{methodnamehyphen}',
                               initkwargs={})

router = routers.DefaultRouter(trailing_slash=False)
router.routes.append(actions_router)
router.register("users", api.UsersViewSet, base_name="users")
router.register("roles", api.RolesViewSet, base_name="roles")
router.register("search", api.Search, base_name="search")

urlpatterns = router.urls
