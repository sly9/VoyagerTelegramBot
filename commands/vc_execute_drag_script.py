from event_emitter import ee
from event_names import BotEvent
from commands.voyager_command_wrapper import VoyagerCommandWrapper
from commands.voyager_command import VoyagerCommand

from commands.supported_commands import SupportedCommands
from typing import Dict


class VCExecuteDragScript(VoyagerCommandWrapper):
    @staticmethod
    def get_command(command_id: int = 1, drag_script_file: str = ''):
        return VoyagerCommand(command_name=str(SupportedCommands.EXECUTE_DRAG_SCRIPT.value), command_id=command_id,
                              params={'DragScriptFile': drag_script_file, 'StartNodeUID': ''})
