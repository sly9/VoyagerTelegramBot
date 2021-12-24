from dataclasses import dataclass


@dataclass
class HostInfo:
    host_name: str = 'localhost'
    url: str = '127.0.0.1'
    port: str = '5950'
    voyager_ver: str = 'unknown'
