import uuid

from django.urls import reverse

from taiga.base.utils.urls import get_absolute_url


# Set this in settings.PROJECT_MODULES_CONFIGURATORS["gogs"]
def get_or_generate_config(project):
    config = project.modules_config.config
    if config and "gogs" in config:
        g_config = project.modules_config.config["gogs"]
    else:
        g_config = {"secret": uuid.uuid4().hex}

    url = reverse("gogs-hook-list")
    url = get_absolute_url(url)
    url = "%s?project=%s" % (url, project.id)
    g_config["webhooks_url"] = url
    return g_config
