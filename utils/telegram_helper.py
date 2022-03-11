import json
from typing import List

import requests

from configs import ConfigBuilder


# Helper to get all available chat ids for Telegram
# Read bot_token from config and then print out all available chat ids

class TelegramHelper:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token
        pass

    def get_chat_ids(self) -> List[int]:
        if self.bot_token is None or self.bot_token == '':
            return list()

        request_url = f'https://api.telegram.org/bot{self.bot_token}/getUpdates'
        response = requests.post(request_url)
        response_json = json.loads(response.text)

        if response_json['ok']:
            # Successfully get response from API
            result = response_json['result']
            chat_ids = set()
            for update_record in result:
                chat_id = update_record['message']['chat']['id']
                chat_ids.add(chat_id)

            return list(chat_ids)
        # default return
        return list()


if __name__ == '__main__':
    config_builder = ConfigBuilder(config_filename='../config.yml')

    if validate_result := config_builder.validate():
        print('validation failed: ', validate_result)
    else:
        config = config_builder.build()

        if config.telegram_setting.bot_token:
            t_helper = TelegramHelper(config.telegram_setting.bot_token)
            print('Available chat ids: ', t_helper.get_chat_ids())
        else:
            print('Please add config of "telegram_setting" > "bot_token" first.')
