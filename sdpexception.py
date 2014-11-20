''' SDP generated exceptions '''

__all__ = [
    'SDPException',
    'SDPDecodeException',
]

class SDPException(Exception):
    ''' General SDP usage error

    This exception can mean any kind of intentional SDP usage error.
    Bugs in code usually raise other exceptions

    SDP.decode() masks it to SDPDecodeException
    '''
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return 'SDP Error: %s' % self.string

class SDPDecodeException(SDPException):
    ''' SDP datagram decode error

    This exception is raised always and only by SDP.decode() method
    when SDP datagram body is malformed
    '''
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return 'Decode error: %s' % self.string
