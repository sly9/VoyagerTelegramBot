import enum


class SupportedCommands(enum.Enum):
    AUTH_USER_BASE = 'AuthenticateUserBase'
    LIST_DRAG_SCRIPT = 'RemoteGetListAvalaibleDragScript'
    EXECUTE_DRAG_SCRIPT = 'RemoteDragScript'
    SET_DASHBOARD_MODE = 'RemoteSetDashboardMode'
    SET_LOG_EVENT = 'RemoteSetLogEvent'
    GET_FILTER_CONFIGS = 'RemoteGetFilterConfiguration'
