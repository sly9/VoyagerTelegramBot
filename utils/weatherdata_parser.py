

class WeatherDataParser:
    def __init__(self, filename):
        self.filename = filename
        self.weather_data_dict = {}

    def update(self):
            with open(self.filename, 'r') as f:
                content = f.read()
                self.weather_data_dict = self.parse_string(content)
    
    def parse_string(self, input_string):
        fields = input_string.split()
        parsed_dict = {
            'file_write_date': fields[0],
            'file_write_time': fields[1],
            'temperature_scale': fields[2],
            'wind_speed_scale': fields[3],
            'sky_temperature': float(fields[4]),
            'ambient_temperature': float(fields[5]),
            'sensor_temperature': float(fields[6]),
            'wind_speed': float(fields[7]),
            'humidity': float(fields[8]),
            'dew_point': float(fields[9]),
            'dew_heater_percentage': int(fields[10]),
            'rain_flag': int(fields[11]),
            'wet_flag': int(fields[12]),
            'elapsed_time': int(fields[13]),
            'elapsed_days': int(fields[14]),
            'cloud_clear_flag': int(fields[15]),
            'wind_limit_flag': int(fields[16]),
            'rain_flag_2': int(fields[17]),
            'darkness_flag': int(fields[18]),
            'roof_close_flag': int(fields[19]),
            'alert_flag': int(fields[20])
        }
        return parsed_dict
