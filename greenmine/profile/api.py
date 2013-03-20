# myapp/api.py
from tastypie.resources import ModelResource
from greenmine.profile.models import *

class ProfileResource(ModelResource):
    class Meta:
        queryset = Profile.objects.all()
        resource_name = 'profile'
