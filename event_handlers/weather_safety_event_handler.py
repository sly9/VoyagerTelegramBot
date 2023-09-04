from typing import Dict

from event_handlers.voyager_event_handler import VoyagerEventHandler
from data_structure.weather_safety import WeatherSafety

# This is just one of the event handlers which are interested in log events. You can write more
class WeatherSafetyHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)
        # it could be either resume or suspend or exit
        self.emergency_status = 'RESUME'
        self.enabled = not self.config.observing_condition_config.send_report_when_emergency_status_changed

    def interested_event_names(self):
        return [
            'LogEvent',
            'WeatherAndSafetyMonitorData', ]

    def handle_event(self, event_name: str, message: Dict):
        if not self.enabled:
            # do nothing if user disables this feature.
            return

        if event_name == 'WeatherAndSafetyMonitorData':
            # maybe this is not worth looking into
            pass

        if event_name == 'LogEvent' and message['Type'] == 9:
            # 9 means emergency.
            try:
                self.process_emergency_string(message['Text'])
            except:
                print("Failed to parse: " + message['Text'])

    def process_emergency_string(self, emergency_string: str):
        # print('EMERGENCY STATUS UPDATED: ' + emergency_string)
        content_string = emergency_string.replace('Voyager Recognize an Emergency Request : ', '')
        new_status = 'RESUME'
        detail_string = ''
        if ' ' in content_string:
            new_status = content_string[:content_string.index(' ')]
            detail_string = content_string[content_string.index(' ')+2:]
        if new_status != self.emergency_status:
            print('EMERGENCY changed from %s to %s' % (self.emergency_status, new_status))
            old_status = self.emergency_status
            self.emergency_status = new_status
        self.parse_detail_string(detail_string, old_status, new_status)

    def parse_detail_string(self, detail_string: str='', old_status: str='', new_status: str='') :
        # source
        weather = self.parse_weather_string(detail_string)
        source = self.parse_source(detail_string)

    def parse_source(self, detail_string: str=''):
        '''

        :param detail_string:
        :return: a combination of 'S' and 'W' ('S' is always before 'W')
        '''
        if 'Source=Safety Monitor' in detail_string:
            return 'S'
        if 'Source=Weather,Safety Monitor' in detail_string:
            return 'SW'
        if 'Source=Weather' in detail_string:
            return 'W'
        return ''

    def parse_weather_string(self, detail_string: str=''):
        if 'Weather String=' not in detail_string:
            return None
        weather_detail = detail_string[detail_string.index('Weather String=') + 15:-1]
        if weather_detail.startswith('n.d.'):

        print (weather_detail)

if __name__ == '__main__':
    from configs import ConfigBuilder
    import json
    config_builder = ConfigBuilder(config_filename='../config.yml', config_template_filename='../config.yml.example')

    if validate_result := config_builder.validate():
        #console.main_console.print(f'validation failed: {validate_result}')
        if validate_result == 'NO_CONFIG_FILE':
            config_builder.copy_template()

        elif validate_result == 'LOAD_CONFIG_FAILED':
            print('Something is clearly wrong with the config!!')
        elif validate_result == 'TEMPLATE_VERSION_DIFFERENCE':
            config_builder.merge()

    config = config_builder.build()
    w = WeatherSafetyHandler(config)
    w.enabled = True
    with open('../tests/emergency.log', 'r') as log_file:
        lines = log_file.readlines()
        for line in lines:
            w.handle_event('LogEvent',json.loads(line))

