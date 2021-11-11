#!/bin/env python3

from collections import defaultdict


class ExposureInfo:
    def __init__(self, filter_name: str = '', exposure_time: int = 0, hfd: float = 0, star_index: float = 0):
        self.filter_name = filter_name.upper()
        # exposure time in seconds
        self.exposure_time = exposure_time
        self.hfd = hfd
        self.star_index = star_index


class SequenceStat:
    def __init__(self, name: str = ''):
        # target name, like 'M31', or 'NGC 6992'
        self.name = name
        self.exposure_info_list = list()
        self.guide_x_error_list = list()  # list of guide error on x axis in pixel
        self.guide_y_error_list = list()  # list of guide error on y axis in pixel

    def add_exposure(self, exposure: ExposureInfo):
        self.exposure_info_list.append(exposure)

    def add_guide_error(self, guide_error: tuple):
        self.guide_x_error_list.append(guide_error[0])
        self.guide_y_error_list.append(guide_error[1])

    def exposure_count(self):
        return len(self.exposure_info_list)

    def exposure_time_stat_dictionary(self):
        """
        Exposure time stats in a dictionary form.
        Key is the filter name, normalized, value is the cumulative time in seconds.
        """
        result = defaultdict(float)
        for expo in self.exposure_info_list:
            result[expo.filter_name] += expo.exposure_time
        return result
