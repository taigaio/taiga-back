# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.utils.translation import ugettext_lazy as _

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Role, User
from .forms import UserChangeForm, UserCreationForm


admin.site.unregister(Group)


class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ('permissions',)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.rel.to.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs['queryset'] = qs.select_related('content_type')
        return super().formfield_for_manytomany(
            db_field, request=request, **kwargs)


# admin.site.register(Role, RoleAdmin)


class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'email', 'bio', 'photo')}),
        (_('Extra info'), {'fields': ('color', 'lang', 'timezone', 'token', 'colorize_tags', 'email_token', 'new_email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_superuser',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('username', 'email', 'full_name')
    list_filter = ('is_superuser', 'is_active')
    search_fields = ('username', 'full_name', 'email')
    ordering = ('username',)
    filter_horizontal = ()

class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


admin.site.register(User, UserAdmin)
