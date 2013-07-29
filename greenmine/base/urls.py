# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url, include
from greenmine.base import api, routers

router = routers.Router(trailing_slash=False)
router.register(r"users", api.UsersViewSet, base_name="users")
router.register(r"roles", api.RolesViewSet, base_name="roles")
router.register(r"search", api.Search, base_name="search")
router.register(r"auth/login", api.Login, base_name="auth-login")
router.register(r"auth/logout", api.Logout, base_name="auth-logout")

urlpatterns = patterns("",
    url(r"", include(router.urls)),
)
