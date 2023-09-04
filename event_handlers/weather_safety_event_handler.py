from typing import Dict

from data_structure.weather_safety import WeatherSafety
from event_handlers.voyager_event_handler import VoyagerEventHandler
import dataclasses

# This is just one of the event handlers which are interested in log events. You can write more
from utils.observing_condition_reporter import ObservingConditionReporter


class WeatherSafetyHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)
        # it could be either resume or suspend or exit
        self.emergency_status = 'RESUME'
        self.enabled = self.config.observing_condition_config.send_report_when_emergency_status_changed

        # latest WeatherSafety data class from 'WeatherAndSafetyMonitorData' event
        self.ws_wasmd = WeatherSafety()
        # latest WeatherSafety data class from 'LogEvent'
        self.ws_log_event = None

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
            self.ws_wasmd = self.process_weather_safety_monitor_event(message)

        if event_name == 'LogEvent' and message['Type'] == 9:
            # 9 means emergency.
            try:
                self.ws_log_event = self.process_emergency_string(message['Text'])
                self.send_observing_condition_report()
            except:
                print("Failed to parse: " + message['Text'])

    def process_weather_safety_monitor_event(self, message: Dict):
        ws = WeatherSafety()
        ws.weather_station_connected = message['WSConnected']
        ws.safe_monitor_connected = message['SMConnected']
        ws.safe_monitor_status = message['SMStatus']
        ws.cloud = message['WSCloud']
        ws.rain = message['WSRain']
        ws.wind = message['WSWind']
        ws.light = message['WSLight']
        return ws

    def process_emergency_string(self, emergency_string: str):
        # print('EMERGENCY STATUS UPDATED: ' + emergency_string)
        content_string = emergency_string.replace('Voyager Recognize an Emergency Request : ', '')
        new_status = 'RESUME'
        old_status = self.emergency_status
        detail_string = ''
        if ' ' in content_string:
            new_status = content_string[:content_string.index(' ')]
            detail_string = content_string[content_string.index(' ') + 2:]
        if new_status != self.emergency_status:
            self.emergency_status = new_status
        ws = self.parse_detail_string(detail_string, old_status, new_status)
        # if ws.old_status != ws.status and ws.status != 'RESUME':
        #     print(ws)
        return ws

    def parse_detail_string(self, detail_string: str = '', old_status: str = '', new_status: str = ''):
        # source
        ws = WeatherSafety()
        ws.old_status = old_status
        ws.status = new_status
        ws.source = self.parse_source(detail_string)
        if 'S' in ws.source: # this is a guess..
            ws.roof = 'CLOSED'
        else:
            ws.roof = 'OPEN'
        self.parse_weather_string(detail_string, ws)
        if new_status == 'RESUME':
            ws.read = 'OK'
        return ws

    def parse_source(self, detail_string: str = ''):
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

    def parse_weather_string(self, detail_string: str = '', ws: WeatherSafety = None):
        if 'Weather String=' not in detail_string:
            return None
        weather_detail = detail_string[detail_string.index('Weather String=') + 15:-1]
        if weather_detail.startswith('n.d.'):
            ws.read = 'n.d.'
            return
        parts = weather_detail.replace('{', '').replace('}', '').split(' - ')
        if len(parts) != 6:
            print('unknown string: ' + weather_detail)
            return
        ws.cloud = parts[0]
        ws.wind = parts[1]
        ws.rain = parts[2]
        ws.light = parts[3]
        ws.read = parts[5]

    def send_observing_condition_report(self):
        # merge two ws
        ws = dataclasses.replace(self.ws_log_event)
        if not ws.cloud:
            ws.cloud = self.ws_wasmd.cloud
        if not ws.wind:
            ws.wind = self.ws_wasmd.wind
        if not ws.rain:
            ws.rain = self.ws_wasmd.rain
        if not ws.light:
            ws.light = self.ws_wasmd.light
        ws.weather_station_connected = self.ws_wasmd.weather_station_connected
        ws.safe_monitor_connected = self.ws_wasmd.safe_monitor_connected
        ws.safe_monitor_status = self.ws_wasmd.safe_monitor_status
        reporter = ObservingConditionReporter(ws=ws)
        reporter.report()


if __name__ == '__main__':
    from configs import ConfigBuilder
    import json

    config_builder = ConfigBuilder(config_filename='../config.yml', config_template_filename='../config.yml.example')

    if validate_result := config_builder.validate():
        # console.main_console.print(f'validation failed: {validate_result}')
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
            w.handle_event('LogEvent', json.loads(line))
