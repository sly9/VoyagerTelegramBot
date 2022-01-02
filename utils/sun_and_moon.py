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


moon_phase_emoji_map = {
    'Full': '🌕',
    'New': '🌑',
    'First Quarter': '🌓',
    'Last Full Quarter': '🌗',
    'Waxing Crescent': '🌒',
    'Waxing Gibbous': '🌔',
    'Waning Gibbous': '🌖',
    'Waning Crescent': '🌘'
}


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

    def human_moon(self):
        target_date_utc = self.observer.date
        target_date_local = ephem.localtime(target_date_utc).date()
        next_full = ephem.localtime(ephem.next_full_moon(target_date_utc)).date()
        next_new = ephem.localtime(ephem.next_new_moon(target_date_utc)).date()
        next_last_quarter = ephem.localtime(ephem.next_last_quarter_moon(target_date_utc)).date()
        next_first_quarter = ephem.localtime(ephem.next_first_quarter_moon(target_date_utc)).date()
        previous_full = ephem.localtime(ephem.previous_full_moon(target_date_utc)).date()
        previous_new = ephem.localtime(ephem.previous_new_moon(target_date_utc)).date()
        previous_last_quarter = ephem.localtime(ephem.previous_last_quarter_moon(target_date_utc)).date()
        previous_first_quarter = ephem.localtime(ephem.previous_first_quarter_moon(target_date_utc)).date()

        waxing, waning = 'Waxing', 'Waning'
        if self.observer.lat < 0:
            waxing, waning = 'Waning', 'Waxing'

        if target_date_local in (next_full, previous_full):
            return 'Full'
        elif target_date_local in (next_new, previous_new):
            return 'New'
        elif target_date_local in (next_first_quarter, previous_first_quarter):
            return 'First Quarter'
        elif target_date_local in (next_last_quarter, previous_last_quarter):
            return 'Last Full Quarter'
        elif previous_new < next_first_quarter < next_full < next_last_quarter < next_new:
            return waxing + ' Crescent'
        elif previous_first_quarter < next_full < next_last_quarter < next_new < next_first_quarter:
            return waxing + ' Gibbous'
        elif previous_full < next_last_quarter < next_new < next_first_quarter < next_full:
            return waning + ' Gibbous'
        elif previous_last_quarter < next_new < next_first_quarter < next_full < next_last_quarter:
            return waning + ' Crescent'

    def moon_emoji(self):
        human_readable_moon_phase = self.human_moon()
        return moon_phase_emoji_map[human_readable_moon_phase]

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
        moon_phase_string = self.human_moon()
        moon_phase_emoji = self.moon_emoji()

        return SunAndMoonDataPoint(sun_altitude=sun_altitude * 180 / math.pi, sunrise_localtime=sunrise,
                                   sunset_localtime=sunset,
                                   astro_twilight_start_localtime=astro_twilight_start,
                                   astro_twilight_end_localtime=astro_twilight_end,
                                   moon_altitude=moon_altitude * 180 / math.pi,
                                   moon_phase=moon.moon_phase, moon_phase_string=moon_phase_string,
                                   moon_phase_emoji=moon_phase_emoji,
                                   moonset_localtime=moonset, moonrise_localtime=moonrise)


if __name__ == '__main__':
    s0 = SunAndMoon(latitude=31.947208, longitude=-108.898106)
    s1 = SunAndMoon(latitude=-10.947208, longitude=-58.898106)

    o0 = s0.observe()
    o1 = s1.observe()
    now = datetime.datetime.now()
    for i in range(100):
        o0 = s0.observe(dt=now)
        o1 = s1.observe(dt=now)
        print(now, o0.moon_phase_emoji, o0.moon_phase_string, o1.moon_phase_emoji, o1.moon_phase_string)
        now = now + datetime.timedelta(days=1)
