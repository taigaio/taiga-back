from taiga.users.models import User


def resolve_users_bindings(users_bindings):
    new_users_bindings = {}
    for key,value in users_bindings.items():
        try:
            user_key = int(key)
        except ValueError:
            user_key = key

        if isinstance(value, str):
            try:
                new_users_bindings[user_key] = User.objects.get(email_iexact=value)
            except User.MultipleObjectsReturned:
                new_users_bindings[user_key] = User.objects.get(email=value)
            except User.DoesNotExists:
                new_users_bindings[user_key] = None
        else:
            new_users_bindings[user_key] = User.objects.get(id=value)
    return new_users_bindings
