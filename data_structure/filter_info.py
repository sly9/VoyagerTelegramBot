class ExposureInfo:
    def __init__(self, filter_name: str = '', exposure_time: int = 0, hfd: float = 0, star_index: float = 0,
                 timestamp: float = 0, sequence_name: str = ''):
        self._filter_name = None
        self.filter_name = filter_name
        # exposure time in seconds
        self.exposure_time = exposure_time
        self.hfd = hfd
        self.star_index = star_index
        self.timestamp = timestamp
        self.sequence_name = sequence_name

    @property
    def filter_name(self) -> str:
        return self._filter_name

    @filter_name.setter
    def filter_name(self, value: str = 'L'):
        filter_alias = {
            'Ha': ['H', 'Ha', 'H-Alpha'],
            'SII': ['S', 'S2', 'SII', 'S-II'],
            'OIII': ['O', 'O3', 'OIII', 'O-III'],
            'L': ['L', 'Lum', 'Luminance'],
            'R': ['R', 'Red'],
            'G': ['G', 'Green'],
            'B': ['B', 'Blue']
        }

        filter_mapping = dict()
        for filter_key in filter_alias:
            for alias in filter_alias[filter_key]:
                filter_mapping[alias.upper()] = filter_key

        if value.upper() in filter_mapping:
            self._filter_name = filter_mapping[value.upper()]
        else:
            # Keep original filter name if no mapping can be found
            self._filter_name = 'UNKNOWN-' + value

    @filter_name.deleter
    def filter_name(self):
        del self._filter_name
