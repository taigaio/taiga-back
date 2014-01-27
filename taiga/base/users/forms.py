# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.forms import (
    UserCreationForm as DjangoUserCreationForm,
    UserChangeForm as DjangoUserChangeForm
)
from .models import User


class UserCreationForm(DjangoUserCreationForm):
    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    class Meta:
        model = User
        fields = ('username',)


class UserChangeForm(DjangoUserChangeForm):
    notify_level = forms.ChoiceField(choices=User.NOTIFY_LEVEL_CHOICES)
    notify_changes_by_me = forms.BooleanField(required=False)

    class Meta:
        model = User

