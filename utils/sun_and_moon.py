import datetime
import math
from dataclasses import dataclass

import ephem
import pytz


@dataclass
class SunAndMoonDataPoint:
    sun_altitude: float = 0
    sunset_localtime: datetime.time = datetime.time()
    sunrise_localtime: datetime.time = datetime.time()
    astro_twilight_start_localtime: datetime.time = datetime.time()
    astro_twilight_end_localtime: datetime.time = datetime.time()

    moon_altitude: float = 0
    moonset_localtime: datetime.time = datetime.time()
    moonrise_localtime: datetime.time = datetime.time()
    moon_phase: float = 0
    moon_phase_string: str = 'Full'
    moon_phase_emoji: str = '🌙'


class SunAndMoon:
    def __init__(self, latitude: float = 0, longitude: float = 0, elevation: float = 0,
                 timezone_name: str = 'US/Mountain'):
        self.observer = ephem.Observer()
        self.observer.lat = str(latitude)
        self.observer.lon = str(longitude)
        self.observer.elevation = elevation
        self.observer.pressure = 0
        self.observer.horizon = '-0:34'

        self.timezone = pytz.timezone(timezone_name)

    def localtime_from_ephem_date(self, date: ephem.Date):
        utc_date_string = date.datetime().isoformat() + '+00:00'
        utc_datetime = datetime.datetime.fromisoformat(utc_date_string)
        return utc_datetime.astimezone(self.timezone).time()

    def observe(self, dt: datetime = datetime.datetime.utcnow()):
        sun = ephem.Sun()

        self.observer.date = dt
        self.observer.horizon = '-0.34'
        sun.compute(self.observer)
        sun_altitude = sun.alt  # type: ephem.Angle

        sunrise = self.localtime_from_ephem_date(self.observer.next_rising(sun))
        sunset = self.localtime_from_ephem_date(self.observer.next_setting(sun))

        # astro twilight
        self.observer.horizon = '-18'
        astro_twilight_end = self.localtime_from_ephem_date(self.observer.next_rising(sun, use_center=True))
        astro_twilight_start = self.localtime_from_ephem_date(self.observer.next_setting(sun, use_center=True))

        self.observer.horizon = '-0.34'

        moon = ephem.Moon()
        moon.compute(self.observer)
        moon_altitude = moon.alt
        moonrise = self.localtime_from_ephem_date(self.observer.next_rising(moon))
        moonset = self.localtime_from_ephem_date(self.observer.next_setting(moon))

        return SunAndMoonDataPoint(sun_altitude=sun_altitude * 180 / math.pi, sunrise_localtime=sunrise,
                                   sunset_localtime=sunset,
                                   astro_twilight_start_localtime=astro_twilight_start,
                                   astro_twilight_end_localtime=astro_twilight_end,
                                   moon_altitude=moon_altitude * 180 / math.pi,
                                   moon_phase=moon.moon_phase, moonset_localtime=moonset, moonrise_localtime=moonrise)


if __name__ == '__main__':
    s = SunAndMoon(latitude=31.947208, longitude=-108.898106)

    o = s.observe()
    now = datetime.datetime.now()
    for i in range(100):
        o = s.observe(dt=now)
        print(o.moon_phase)
        now = now + datetime.timedelta(days=1)
