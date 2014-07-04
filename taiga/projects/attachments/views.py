import os

from django.conf import settings
from django import http

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from . import permissions
from . import models


def serve_attachment(request, attachment):
    if settings.IN_DEVELOPMENT_SERVER:
        return http.HttpResponseRedirect(attachment.url)

    name = attachment.name
    response = http.HttpResponse()
    response['X-Accel-Redirect'] = "/{filepath}".format(filepath=name)
    response['Content-Disposition'] = 'attachment;filename={filename}'.format(
        filename=os.path.basename(name))

    return response


class RawAttachmentView(generics.RetrieveAPIView):
    queryset = models.Attachment.objects.all()
    permission_classes = (IsAuthenticated, permissions.AttachmentPermission,)

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        return serve_attachment(request, self.object.attached_file)
