class MissingData(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'MissingData Exception: {}'.format(self.msg)