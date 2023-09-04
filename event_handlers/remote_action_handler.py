from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent
from typing import Dict

from commands.vc_list_drag_script import VCListDragScript
from commands.supported_commands import SupportedCommands


class RemoteActionHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)

    def interested_event_name(self):
        return 'RemoteActionResult'

    def handle_event(self, event_name: str, message: Dict):
        if event_name == 'RemoteActionResult':
            self.handle_remote_action_event(message)

    def handle_remote_action_event(self, message: Dict):
        if message['MethodName'] == SupportedCommands.LIST_DRAG_SCRIPT.value:
            VCListDragScript.parse_response(message)
