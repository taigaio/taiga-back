"""
This model contains a domain logic for users application.
"""

from django.db.models.loading import get_model
from taiga.base import exceptions as exc


def get_and_validate_user(*, username:str, password:str) -> bool:
    """
    Check if user with username exists and specified
    password matchs well with existing user password.

    if user is valid,  user is returned else, corresponding
    exception is raised.
    """

    user_model = get_model("users", "User")
    qs = user_model.objects.filter(username=username)
    if len(qs) == 0:
        raise exc.WrongArguments("Username or password does not matches user.")

    user = qs[0]
    if not user.check_password(password):
        raise exc.WrongArguments("Username or password does not matches user.")

    return user
