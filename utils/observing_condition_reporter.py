from data_structure.weather_safety import WeatherSafety
from event_emitter import ee
from event_names import BotEvent


class ObservingConditionReporter:
    def __init__(self, ws:WeatherSafety):
        self.ws = ws

    def report(self):
        '''
        This method will be preparing a nice looking image, containing running status, security camera, all sky camera
        :return:
        '''
        ws = self.ws
        if ws.old_status != ws.status:
            status_change_str = ''
            if ws.status == 'RESUME':
                status_change_str = 'Resuming observing...'
            elif ws.status == 'SUSPEND':
                status_change_str = 'Suspending observing...'
            elif ws.status == 'EXIT':
                status_change_str = 'Exit observing...'
            ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, status_change_str)
        if ws.status != 'RESUME':
            if ws.read != 'OK':
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, 'Can\'t read status files.. please check roof computer')
            else:
                bad_reasons = []
                if ws.roof != 'OPEN':
                    bad_reasons.append('Roof Closed')
                if ws.cloud != 'CLEAR':
                    bad_reasons.append(ws.cloud)
                if ws.wind != 'CALM':
                    bad_reasons.append(ws.wind)
                if ws.rain != 'DRY':
                    bad_reasons.append(ws.rain)
                if ws.light != 'DARK':
                    bad_reasons.append(ws.light)
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, 'Reason for not observing: ' +', '.join(bad_reasons) )
        ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, str(ws))


