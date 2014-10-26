import tornado.web

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'FileHandler',
    'get',
]

class FileHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render(args[0])
