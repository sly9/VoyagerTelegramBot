from event_emitter import ee
from event_names import BotEvent
from commands.voyager_command_wrapper import VoyagerCommandWrapper
from commands.voyager_command import VoyagerCommand

from commands.supported_commands import SupportedCommands
from typing import Dict


class VCListDragScript(VoyagerCommandWrapper):
    @staticmethod
    def get_command(command_id: int = 1):
        return VoyagerCommand(command_name=str(SupportedCommands.LIST_DRAG_SCRIPT.value), command_id=command_id,
                              params=dict())

    @staticmethod
    def parse_response(response: Dict):
        drag_script_list = response['ParamRet']['list']
        ee.emit(BotEvent.RECEIVE_DRAG_SCRIPT_LIST.name, drag_script_list=drag_script_list)
