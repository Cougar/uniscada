import tornado.web
import json

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'UnknownHandler',
    'get',
]

class UnknownHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self, *args, **kwargs):
        self.set_status(404)
        base_url = self.request.protocol + '://' + self.request.host
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({
            'message': 'Not Found',
            'api_url': base_url + '/api/v1/'
        }, indent = 4, sort_keys = True))
        self.finish()
