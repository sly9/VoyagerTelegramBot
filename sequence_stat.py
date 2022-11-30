#!/bin/env python3
import gc
import io
import math
from collections import defaultdict, deque
from datetime import datetime
from statistics import mean, stdev
from typing import Tuple

import matplotlib
import numpy as np
from colour import Color
from matplotlib import axes
from matplotlib import pyplot as plt
from matplotlib.dates import ConciseDateFormatter, AutoDateLocator

from data_structure.filter_info import ExposureInfo
from data_structure.focus_result import FocusResult

matplotlib.use('agg')


class SequenceStat:
    def __init__(self, name: str = ''):
        # target name, like 'M31', or 'NGC 6992'
        self.name = name
        self.existing_exposure_info_list = list()
        self.exposure_info_list = list()
        self.focus_result_list = list()
        self.guide_x_error_list = list()  # list of guide error on x axis in pixel
        self.guide_y_error_list = list()  # list of guide error on y axis in pixel

    def merge_existing_exposure_info(self, existing_exposure_info_dict: dict) -> None:
        for filter_name, exposure_time in existing_exposure_info_dict.items():
            exposure = ExposureInfo(filter_name=filter_name, exposure_time=exposure_time, sequence_target=self.name)
            self.existing_exposure_info_list.append(exposure)

    def add_exposure(self, exposure: ExposureInfo) -> None:
        self.exposure_info_list.append(exposure)

    def add_focus_result(self, focus_result: FocusResult):
        focus_result.recommended_index = self.exposure_count() - 0.5
        self.focus_result_list.append(focus_result)

    def add_guide_error(self, guide_error: tuple):
        if len(self.guide_x_error_list) > 0 and self.guide_x_error_list[-1] == guide_error[0] and \
                self.guide_y_error_list[-1] == guide_error[1]:
            return
        self.guide_x_error_list.append(guide_error[0])
        self.guide_y_error_list.append(guide_error[1])

    def exposure_count(self):
        return len(self.exposure_info_list)

    def new_exposure_time_stat_dictionary(self):
        """
        Exposure time stats in a dictionary form.
        Key is the target_name+filter name, normalized. Value is a pair of seconds, the first value is the cumulative
        exposure time recorded today, while the second value is the previously accumulated results.
        """
        result = defaultdict(lambda: (0.0, 0.0))
        for expo in self.exposure_info_list:
            key = expo.sequence_target + ' ' + expo.filter_name
            left, right = result[key]
            result[key] = (left + expo.exposure_time, right)
        for expo in self.existing_exposure_info_list:
            key = expo.sequence_target + ' ' + expo.filter_name
            left, right = result[key]
            result[key] = (left, right + expo.exposure_time)
        return result

    def exposure_time_stat_dictionary(self):
        """
        Exposure time stats in a dictionary form.
        Key is the target_name+filter name, normalized, value is the cumulative time in seconds.
        """
        result = defaultdict(float)
        for expo in self.exposure_info_list:
            result[expo.sequence_target + ' ' + expo.filter_name] += expo.exposure_time
        return result


class StatPlotter:
    def __init__(self, config: dict = None):
        self.plotter_configs = config.sequence_stats_config

        plt.ioff()
        plt.rcParams.update({'text.color': '#F5F5F5', 'font.size': 40, 'font.weight': 'bold',
                             'axes.edgecolor': '#F5F5F5', 'figure.facecolor': '#212121',
                             'xtick.color': '#F5F5F5', 'ytick.color': '#F5F5F5'})

        self.figure_count = len(self.plotter_configs.types)
        self.filter_meta = self.plotter_configs.filter_styles

    def _circle(self, ax: axes.Axes = None, origin: Tuple[float, float] = (0, 0), radius: float = 1.0, **kwargs):
        angle = np.linspace(0, 2 * np.pi, 150)
        x = radius * np.cos(angle) + origin[0]
        y = radius * np.sin(angle) + origin[1]

        ax.plot(x, y, **kwargs)

    def hfd_plot(self, ax: axes.Axes = None, sequence_stat: SequenceStat = None, target_name: str = ''):
        img_ids = range(sequence_stat.exposure_count())
        hfd_values = list()
        dot_colors = list()
        star_indices = list()
        seeing_values = list()
        for exposure_info in sequence_stat.exposure_info_list:
            hfd_values.append(exposure_info.hfd)
            star_indices.append(exposure_info.star_index)
            seeing_values.append(exposure_info.seeing)
            if exposure_info.filter_name in self.filter_meta:
                color = self.filter_meta[exposure_info.filter_name]['color']
            else:
                color = '#660874'

            dot_colors.append(color)

        ax.set_facecolor('#212121')

        # focus results:
        if len(sequence_stat.focus_result_list):
            focus_index = list()
            focus_hfd_value = list()
            focus_colors = list()
            for focus_result in sequence_stat.focus_result_list:
                focus_hfd_value.append(focus_result.hfd)
                focus_colors.append(focus_result.filter_color)
                focus_index.append(focus_result.recommended_index)
            ax.scatter(focus_index, focus_hfd_value, c=focus_colors, s=1000, zorder=2)

        # Seeing results:
        ax.plot(img_ids, seeing_values, color='#888', linewidth=5, zorder=1)
        ax.scatter(img_ids, seeing_values, c=dot_colors, s=500, zorder=1)

        # hfd and star index
        ax.plot(img_ids, hfd_values, color='#FF9800', linewidth=10, zorder=1)
        ax.scatter(img_ids, hfd_values, c=dot_colors, s=500, zorder=2)
        ax.tick_params(axis='y', labelcolor='#FFB74D')
        ax.set_ylabel('HFD', color='#FFB74D')

        secondary_ax = ax.twinx()
        secondary_ax.plot(img_ids, star_indices, color='#9C27B0', linewidth=10, zorder=1)
        secondary_ax.scatter(img_ids, star_indices, c=dot_colors, s=500, zorder=2)
        secondary_ax.tick_params(axis='y', labelcolor='#BA68C8')
        secondary_ax.set_ylabel('Star Index', color='#BA68C8')

        ax.set_xlabel('Image Index')
        ax.xaxis.label.set_color('#F5F5F5')
        ax.set_title('HFD and StarIndex Plot ({target})'.format(target=target_name))

    def exposure_plot(self, ax: axes.Axes = None, sequence_stat: SequenceStat = None, target_name: str = ''):
        ax.set_facecolor('#212121')
        total_exposure_stat = sequence_stat.new_exposure_time_stat_dictionary()
        keys = list(total_exposure_stat.keys())
        today_exposure_values = list(map(lambda x: total_exposure_stat[x][0], keys))

        def seconds_to_readable_hours(seconds):
            if seconds == 0:
                return ''
            hours = int(math.floor(seconds / 3600))
            minutes = int(math.floor((seconds - hours * 3600) / 60))
            sec = int(seconds % 60)
            if hours > 0:
                return f'{hours}:{minutes:02d}:{sec:02d}'
            else:
                return f'{minutes:02d}:{sec:02d}'

        previously_exposure_values = list(map(lambda x: total_exposure_stat[x][1], keys))

        previous_rectangles = ax.bar(keys, previously_exposure_values)
        today_rectangles = ax.bar(keys, today_exposure_values, bottom=previously_exposure_values)
        for i in range(len(keys)):
            filter_name = keys[i].split()[-1]
            if filter_name in self.filter_meta:
                color = self.filter_meta[filter_name]['color']
            else:
                color = '#660874'
            rect = today_rectangles[i]
            rect.set_color(color)
            previous_color = Color(color)
            previous_color.set_saturation(previous_color.get_saturation() * 0.7)
            previous_color.set_luminance(previous_color.get_luminance() * 0.7)
            previous_rectangles[i].set_color(previous_color.hex)

        x_bound_lower, x_bound_higher = ax.get_xbound()
        y_bound_lower, y_bound_higher = ax.get_ybound()
        ax.set_xbound(x_bound_lower - 0.3, x_bound_higher + 0.3)
        ax.set_ybound(y_bound_lower, y_bound_higher * 1.1)

        today_exposure_labels = list(map(lambda x: seconds_to_readable_hours(total_exposure_stat[x][0]), keys))
        previously_exposure_labels = list(map(lambda x: seconds_to_readable_hours(total_exposure_stat[x][1]), keys))

        ax.bar_label(previous_rectangles, label_type='center', labels=previously_exposure_labels, fontsize=48)
        ax.bar_label(today_rectangles, label_type='center', labels=today_exposure_labels, fontsize=48)

        ax.set_ylabel('Exposure Time(s)')
        ax.yaxis.label.set_color('#F5F5F5')
        ax.set_title('Cumulative Exposure Time by Filter ({target})'.format(target=target_name))

    def memory_history_plot(self, ax: axes.Axes = None, memory_history: deque = deque()):
        voyager_physical_memory = [x.voyager_rss for x in memory_history]
        voyager_virtual_memory = [x.voyager_vms for x in memory_history]
        bot_physical_memory = [x.bot_rss for x in memory_history]
        bot_virtual_memory = [x.bot_vms for x in memory_history]

        time_series = [datetime.fromtimestamp(x.timestamp) for x in memory_history]
        ax.set_facecolor('#212121')

        locator = AutoDateLocator()
        formatter = ConciseDateFormatter(locator=locator)

        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_major_locator(locator)

        for memory_usage in memory_history:
            if memory_usage.oom_observed:
                ax.axvline(x=datetime.fromtimestamp(memory_usage.timestamp), color='#FF6D00')

        # hfd and star index
        ax.plot(time_series, voyager_physical_memory, color='#F44336', linewidth=10, zorder=1)
        ax.plot(time_series, voyager_virtual_memory, color='#B71C1C', linewidth=10, zorder=1)
        ax.plot(time_series, bot_virtual_memory, color='#2196F3', linewidth=10, zorder=1)
        ax.plot(time_series, bot_physical_memory, color='#3F51B5', linewidth=10, zorder=1)

        ax.tick_params(axis='y', labelcolor='#F44336')
        ax.set_ylabel('Memory(MB)', color='#F44336')

        ax.set_xlabel('Time')
        ax.xaxis.label.set_color('#F5F5F5')
        ax.set_title('Physical and virtual memory usage for voyager and bot')

    def guiding_plot(self, ax_main: axes.Axes = None, ax_scatter: axes.Axes = None, sequence_stat: SequenceStat = None,
                     target_name: str = ''):
        config = self.plotter_configs.guiding_error_plot
        ax_main.set_facecolor('#212121')
        ax_main.plot(sequence_stat.guide_x_error_list, color='#F44336', linewidth=2)
        ax_main.plot(sequence_stat.guide_y_error_list, color='#2196F3', linewidth=2)
        ax_main.axhline(0, color='white')

        abs_x_list = list()
        abs_y_list = list()
        distance_list = list()
        for idx, x_error in enumerate(sequence_stat.guide_x_error_list):
            y_error = sequence_stat.guide_y_error_list[idx]
            abs_x_list.append(abs(x_error))
            abs_y_list.append(abs(y_error))
            distance_list.append(np.sqrt(x_error ** 2 + y_error ** 2))

        smoothing_window_size = 50
        if len(distance_list) > smoothing_window_size:
            box = np.ones(smoothing_window_size) / smoothing_window_size
            smooth_distance_array = np.convolve(distance_list, box, mode='same')
            smooth_distance_array_negative = [-x for x in smooth_distance_array]
            ax_main.fill_between(
                range(len(smooth_distance_array)),
                smooth_distance_array_negative,
                smooth_distance_array,
                alpha=0.4, color='green')

        unit = 'Pixel' if config['unit'] == 'PIXEL' else 'Arcsec'
        scale = 1.0 if config['unit'] == 'PIXEL' else float(config['scale'])

        unit_short = 'px'
        if config['unit'] == 'ARCSEC':
            unit_short = '"'

        title_template = 'Guiding Plot (avg(abs)/min/max/std), unit: {unit}\n' \
                         'X={x_mean:.03f}{unit_short}/{x_min:.03f}{unit_short}/{x_max:.03f}{unit_short}/{x_std:.03f}{unit_short}\n' \
                         'Y={y_mean:.03f}{unit_short}/{y_min:.03f}{unit_short}/{y_max:.03f}{unit_short}/{y_std:.03f}{unit_short}\n' \
                         'Total RMS: mean={t_mean:.03f}{unit_short}/95P={t_95:.03f}{unit_short}/STD={t_std:.03f}{unit_short}'

        ax_main.set_title(title_template.format(
            unit=unit,
            unit_short=unit_short,
            x_mean=mean(abs_x_list),
            x_min=min(sequence_stat.guide_x_error_list) * scale,
            x_max=max(sequence_stat.guide_x_error_list) * scale,
            x_std=stdev(sequence_stat.guide_x_error_list) * scale if len(
                sequence_stat.guide_x_error_list) >= 2 else 0.0,
            y_mean=mean(abs_y_list) * scale,
            y_min=min(sequence_stat.guide_y_error_list) * scale,
            y_max=max(sequence_stat.guide_y_error_list) * scale,
            y_std=stdev(sequence_stat.guide_y_error_list) * scale if len(
                sequence_stat.guide_y_error_list) >= 2 else 0.0,
            t_mean=mean(distance_list) * scale,
            t_95=np.percentile(distance_list, 95) * scale,
            t_std=stdev(distance_list) * scale if len(distance_list) >= 2 else 0.0,
        ))

        ax_scatter.set_facecolor('#212121')
        ax_scatter.set_aspect('equal', 'datalim')

        ax_scatter.tick_params(axis="x", labelbottom=False, labeltop=True, width=5)
        ax_scatter.tick_params(axis="y", labelleft=True, width=5)
        if hasattr(self.plotter_configs, 'guiding_error_plot') and \
                self.plotter_configs.guiding_error_plot.get('error_boundary'):
            boundary = self.plotter_configs.guiding_error_plot.get('error_boundary')
            ax_scatter.set_xlim([-boundary, boundary])
            ax_scatter.set_ylim([-boundary, boundary])
        # https://material.io/archive/guidelines/style/color.html#color-color-palette
        self._circle(ax=ax_scatter, origin=(0, 0), radius=2, linestyle='--', color='#66BB6A', linewidth=2)
        self._circle(ax=ax_scatter, origin=(0, 0), radius=1, linestyle='--', color='#66BB6A', linewidth=2)

        self._circle(ax=ax_scatter, origin=(0, 0), radius=mean(distance_list) * scale, linestyle='-', color='#B2EBF2',
                     linewidth=4)
        self._circle(ax=ax_scatter, origin=(0, 0), radius=np.percentile(distance_list, 95) * scale, linestyle='-',
                     color='#B2EBF2',
                     linewidth=4)
        guide_x_error_list = [element * scale for element in sequence_stat.guide_x_error_list]
        guide_y_error_list = [element * scale for element in sequence_stat.guide_y_error_list]

        ax_scatter.scatter(x=guide_x_error_list, y=guide_y_error_list, color='#26C6DA')

    def plot(self, sequence_stat: SequenceStat = None, memory_history: deque = deque()):
        if sequence_stat is None:
            return

        fig = plt.figure(figsize=(30, 10 * self.figure_count), constrained_layout=True)

        if 'GuidingPlot' in self.plotter_configs.types:
            gridspec = fig.add_gridspec(nrows=self.figure_count, ncols=2,
                                        height_ratios=[1] * self.figure_count, width_ratios=[0.68, 0.32])
        else:
            gridspec = fig.add_gridspec(nrows=self.figure_count, ncols=1,
                                        height_ratios=[1] * self.figure_count, width_ratios=[1])

        figure_index = 0
        if 'HFDPlot' in self.plotter_configs.types:
            ax = fig.add_subplot(gridspec[figure_index, :])
            self.hfd_plot(ax=ax, sequence_stat=sequence_stat, target_name=sequence_stat.name)
            figure_index += 1

        if 'ExposurePlot' in self.plotter_configs.types:
            ax = fig.add_subplot(gridspec[figure_index, :])
            self.exposure_plot(ax=ax, sequence_stat=sequence_stat, target_name=sequence_stat.name)
            figure_index += 1

        if 'MemoryHistoryPlot' in self.plotter_configs.types:
            ax = fig.add_subplot(gridspec[figure_index, :])
            self.memory_history_plot(ax=ax, memory_history=memory_history)
            figure_index += 1

        if 'GuidingPlot' in self.plotter_configs.types and len(sequence_stat.guide_x_error_list) > 0:
            ax_main = fig.add_subplot(gridspec[figure_index:figure_index + 2, 0])
            ax_scatter = fig.add_subplot(gridspec[figure_index, 1])

            self.guiding_plot(ax_main=ax_main, ax_scatter=ax_scatter, sequence_stat=sequence_stat,
                              target_name=sequence_stat.name)
            figure_index += 1

        # fig.tight_layout()

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='jpg')
        img_bytes.seek(0)
        image_data = img_bytes.read()

        # Prevent RuntimeWarning 'More than 20 figures have been opened' from matplotlib
        plt.close('all')
        plt.close()
        img_bytes.close()
        gc.collect()
        return image_data
