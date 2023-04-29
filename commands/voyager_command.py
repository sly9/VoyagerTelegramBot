import uuid
from typing import Dict


class VoyagerCommand:
    def __init__(self, command_name: str = '', command_id: int = 1, params: Dict = None):
        super()
        self.method = command_name
        self.params = params
        self.id = command_id
        self.assign_uuid()

    def add_or_replace_param(self, key: str = '', value=None):
        if not self.params:
            self.params = dict()

        self.params[key] = value

    def assign_uuid(self):
        command_uuid = str(uuid.uuid1())
        self.add_or_replace_param(key='UID', value=command_uuid)

    def get_command_dict(self):
        return {'method': self.method, 'params': self.params, 'id': self.id}
