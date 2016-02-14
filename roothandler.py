import tornado.web
import json

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'RootHandler',
    'get',
]

class RootHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self, *args, **kwargs):
        base_url = self.request.protocol + '://' + self.request.host
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.set_header("Strict-Transport-Security", "max-age=31536000")
        self.set_header("Content-Security-Policy", "default-src 'none';")
        self.set_header("X-Frame-Options", "deny")
        self.set_header("X-Xss-Protection", "1; block")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("X-Content-Type-Options", "nosniff")
        self.set_header("Server", "apiserver")
        self.write(json.dumps({
            'hostgroup_url': base_url + '/api/v1/hostgroups{/name}',
            'servicegroup_url': base_url + '/api/v1/servicegroups{/name}',
            'service_url': base_url + '/api/v1/services/name',
            'websocket_url': base_url.replace('http', 'ws', 1) + '/api/v1/ws'
        }, indent = 4, sort_keys = True))
        self.finish()
