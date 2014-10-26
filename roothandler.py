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
        self.write(json.dumps({
            'hostgroup_url': base_url + '/api/v1/hostgroups{/name}',
            'servicegroup_url': base_url + '/api/v1/servicegroups{/name}',
            'service_url': base_url + '/api/v1/services/name',
            'websocket_url': base_url.replace('http', 'ws', 1) + '/api/v1/ws'
        }, indent = 4, sort_keys = True))
        self.finish()
