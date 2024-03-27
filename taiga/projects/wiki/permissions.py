# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import (TaigaResourcePermission, HasProjectPerm,
                                        IsAuthenticated, IsProjectAdmin, AllowAny,
                                        IsSuperUser)

from taiga.permissions.permissions import CommentAndOrUpdatePerm


class WikiPagePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_wiki_pages')
    by_slug_perms = HasProjectPerm('view_wiki_pages')
    create_perms = HasProjectPerm('add_wiki_page')
    update_perms = CommentAndOrUpdatePerm('modify_wiki_page', 'comment_wiki_page')
    partial_update_perms = CommentAndOrUpdatePerm('modify_wiki_page', 'comment_wiki_page')
    destroy_perms = HasProjectPerm('delete_wiki_page')
    list_perms = AllowAny()
    render_perms = AllowAny()
    watch_perms = IsAuthenticated() & HasProjectPerm('view_wiki_pages')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_wiki_pages')


class WikiPageWatchersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_wiki_pages')
    list_perms = HasProjectPerm('view_wiki_pages')


class WikiLinkPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_wiki_links')
    create_perms = HasProjectPerm('add_wiki_link')
    update_perms = HasProjectPerm('modify_wiki_link')
    partial_update_perms = HasProjectPerm('modify_wiki_link')
    destroy_perms = HasProjectPerm('delete_wiki_link')
    list_perms = AllowAny()
    create_wiki_page_perms = HasProjectPerm('add_wiki_page')
