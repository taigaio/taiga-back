from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.issues.models import Issue
from taiga.projects.models import Project

from . import sequences as seq


class Reference(models.Model):
    content_type = models.ForeignKey(ContentType, related_name="+")
    object_id = models.PositiveIntegerField()
    ref = models.BigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey("projects.Project", null=False,
                                blank=False, related_name="references")

    class Meta:
        ordering = ["created_at"]
        unique_together = ["project", "ref"]

    def __str__(self):
        return "Reference {}".format(self.object_id)


def make_sequence_name(project) -> str:
    return "references_project{0}".format(project.pk)


def make_unique_reference_id(project, *, create=False):
    seqname = make_sequence_name(project)
    if create and not seq.exists(seqname):
        seq.create(seqname)
    return seq.next_value(seqname)


def make_reference(instance, project, create=False):
    refval = make_unique_reference_id(project, create=create)
    ct = ContentType.objects.get_for_model(instance.__class__)
    refinstance = Reference.objects.create(content_type=ct,
                                           object_id=instance.pk,
                                           ref=refval,
                                           project=project)
    return refval, refinstance


def create_sequence(sender, instance, created, **kwargs):
    if not created:
        return

    seqname = make_sequence_name(instance)
    if not seq.exists(seqname):
        seq.create(seqname)

def attach_sequence(sender, instance, created, **kwargs):
    if created:
        # Create a reference object. This operation should be
        # used in transaction context, otherwise it can
        # create a lot of phantom reference objects.
        refval, _ = make_reference(instance, instance.project)

        # Additionally, attach sequence number to instance as ref
        instance.ref = refval
        instance.save(update_fields=['ref'])


models.signals.post_save.connect(create_sequence, sender=Project, dispatch_uid="refproj")
models.signals.post_save.connect(attach_sequence, sender=UserStory, dispatch_uid="refus")
models.signals.post_save.connect(attach_sequence, sender=Issue, dispatch_uid="refissue")
models.signals.post_save.connect(attach_sequence, sender=Task, dispatch_uid="reftask")




