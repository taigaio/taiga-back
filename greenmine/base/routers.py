# -*- coding: utf-8 -*-

from rest_framework import routers

# Special router for actions.
actions_router = routers.Route(url=r'^{prefix}/actions/{methodname}{trailing_slash}$',
                               mapping={'{httpmethod}': '{methodname}'},
                               name='{basename}-{methodnamehyphen}',
                               initkwargs={})

class Router(routers.DefaultRouter):
    routes = routers.DefaultRouter.routes + [actions_router]
