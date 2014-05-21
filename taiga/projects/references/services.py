from .models import Reference

def get_instance_by_ref(project_id, obj_ref):
    try:
        instance = Reference.objects.get(project_id=project_id, ref=obj_ref)
    except Reference.DoesNotExist:
        instance = None

    return instance
