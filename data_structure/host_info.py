import enum
from dataclasses import dataclass


class VoyagerConnectionStatus(enum.Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class VoyagerAuthenticationStatus(enum.Enum):
    SUCCESS = 0
    AUTHENTICATING = 1
    AUTHENTICATION_FAILED = 2


@dataclass
class HostInfo:
    host_name: str = 'localhost'
    url: str = '127.0.0.1'
    port: str = '5950'
    voyager_ver: str = 'unknown'
    connection_status: VoyagerConnectionStatus = VoyagerConnectionStatus.DISCONNECTED
    authentication_status: VoyagerAuthenticationStatus = VoyagerAuthenticationStatus.SUCCESS
