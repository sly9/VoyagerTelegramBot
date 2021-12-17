class HostInfo:
    def __init__(self, host_name: str = 'localhost', url: str = '127.0.0.1', port: str = '5950', voyager_ver='unknown'):
        self.host_name = host_name
        self.url = url
        self.port = port
        self.voyager_ver = voyager_ver
