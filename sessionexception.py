class SessionException(Exception):
    def __init__(self, string):
        self.string = string
    def __str__(self):
        return 'Session Error: %s' % self.string


