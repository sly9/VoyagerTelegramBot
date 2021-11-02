#!/bin/env python3

from telegram import TelegramBot
from datetime import datetime

class VoyagerClient:    
    def parse_message(self, event, message):
        if event == 'NewJPGReady':
            self.handle_jpg_ready(message)
        elif event == 'AutoFocusResult':
            self.handle_focus_result(message)
        elif event == 'LogEvent':
            self.handle_log(message)
        elif event == 'ControlData' or event == 'ShotRunning' or event == 'Polling':
            #do nothing
            message.pop('Event', None)
            message.pop('Host', None)
            message.pop('Inst', None)
            print('.', end = '',flush=True)
        else:
            timestamp = message['Timestamp']
            message.pop('Timestamp', None)
            print('[%s][%s]: %s' % (datetime.fromtimestamp(timestamp), event, message))

    def handle_focus_result(self, message):
        is_empty =  message['IsEmpty']
        if is_empty:
            return
        done = message['Done']
        last_error = message['LastError']
        if not done:
            TelegramBot.send_text_message('Auto focusing failed with reason: %s' % last_error)
            return        
        filter_index =  message['FilterIndex']
        filter_color =  message['FilterColor']
        HFD = message['HFD']
        star_index = message['StarIndex']
        focus_temp = message['FocusTemp']
        position = message['Position']
        telegram_message = 'AutoFocusing for filter %d is done with position %d, HFD: %f' %(filter_index,position, HFD) 
        TelegramBot.send_text_message(telegram_message)

    def handle_jpg_ready(self, message):
        expo = message['Expo']
        filter_name =  message['Filter']
        sequence_target =  message['SequenceTarget']
        HFD = message['HFD']
        star_index = message['StarIndex']
        base64_photo = message['Base64Data']
        telegram_message = 'Exposure of %s for %dsec using %s filter. HFD: %.2f, StarIndex: %.2f' % (sequence_target, expo, filter_name, HFD, star_index)
        if expo > 5:
            fit_filename = message['File']
            new_filename = fit_filename[fit_filename.rindex('\\')+1: fit_filename.index('.')]+'.jpg'
            TelegramBot.send_base64_photo(base64_photo,new_filename, telegram_message)
        else:
            TelegramBot.send_text_message(telegram_message)

        
    def handle_log(self, message):
        type_dict = {1:'DEBUG',2:'INFO',3: 'WARNING',4: 'CRITICAL',5 :'ACTION',6:'SUBTITLE',7: 'EVENT',8: 'REQUEST',9: 'EMERGENCY'}
        type_name = type_dict[message['Type']]
        content = '[%s]%s' %(type_name, message['Text'])
        telegram_message = '<b><pre>%s</pre></b>' % content
        print(content)
        if message['Type'] != 3 and message['Type'] != 4 and message['Type'] != 5 and message['Type'] != 9:
            return
        TelegramBot.send_text_message(telegram_message)
