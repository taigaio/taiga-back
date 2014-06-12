from django.db.models.loading import get_model


def get_instance_by_ref(project_id, obj_ref):
    model_cls = get_model("references", "Reference")
    try:
        instance = model_cls.objects.get(project_id=project_id, ref=obj_ref)
    except model_cls.DoesNotExist:
        instance = None

    return instance
