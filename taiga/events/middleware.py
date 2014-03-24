import threading

_local = threading.local()
_local.session_id = None


def get_current_session_id() -> str:
    """
    Get current session id for current
    request.

    This function should be used only whithin
    request context. Out of request context
    it always return None
    """

    global _local
    if not hasattr(_local, "session_id"):
        raise RuntimeException("No session identifier is found, "
                               "ara you sure that session id middleware "
                               "is active?")
    return _local.session_id


class SessionIDMiddleware(object):
    """
    Middleware for extract and store a current web sesion
    identifier to thread local storage (that only avaliable for
    current thread).
    """

    def process_request(self, request):
        global _local
        session_id = request.META.get("HTTP_X_SESSION_ID", None)
        _local.session_id = session_id
        request.session_id = session_id

    def process_response(self, request, response):
        global _local
        _local.session_id = None

        return response
