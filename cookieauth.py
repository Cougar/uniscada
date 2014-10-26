import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'CookieAuth',
    'get_current_user',
]

class CookieAuth:
    def __init__(self, handler):
        self.handler = handler

    def get_current_user(self):
        # FIXME: cookie check
        try:
            cookeiauth = self.handler.get_cookie('itvilla_com', None)
            if cookeiauth == None:
                return None
            return cookeiauth.split(':')[0]
        except:
            return None
