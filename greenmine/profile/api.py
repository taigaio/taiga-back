# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization

from greenmine.profile.models import Profile


class ProfileResource(ModelResource):
    class Meta:
        queryset = Profile.objects.all()
        resource_name = 'profile'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
