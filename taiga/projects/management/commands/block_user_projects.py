# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from taiga.projects.choices import BLOCKED_BY_NONPAYMENT
from taiga.projects.models import Project


class Command(BaseCommand):
    help = "Block user projects"

    def add_arguments(self, parser):
        parser.add_argument("owner_usernames",
                            nargs="+",
                            help="<owner_usernames owner_usernames ...>")

        parser.add_argument("--is-private",
                            dest="is_private")

        parser.add_argument("--blocked-code",
                            dest="blocked_code")

    def handle(self, *args, **options):
        owner_usernames = options["owner_usernames"]
        projects = Project.objects.filter(owner__username__in=owner_usernames)

        is_private = options.get("is_private")
        if is_private is not None:
            is_private = is_private.lower()
            is_private = is_private[0] in ["t", "y", "1"]
            projects = projects.filter(is_private=is_private)

        blocked_code = options.get("blocked_code")
        blocked_code = blocked_code if blocked_code is not None else BLOCKED_BY_NONPAYMENT
        projects.update(blocked_code=blocked_code)
