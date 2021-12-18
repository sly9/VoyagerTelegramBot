#!/bin/env python3
import base64
import io
from collections import defaultdict
from statistics import mean, stdev
from typing import Tuple

import numpy as np
from matplotlib import axes
from matplotlib import pyplot as plt

from data_structure.filter_info import ExposureInfo
from data_structure.focus_result import FocusResult


class SequenceStat:
    def __init__(self, name: str = ''):
        # target name, like 'M31', or 'NGC 6992'
        self.name = name
        self.exposure_info_list = list()
        self.focus_result_list = list()
        self.guide_x_error_list = list()  # list of guide error on x axis in pixel
        self.guide_y_error_list = list()  # list of guide error on y axis in pixel

    def add_exposure(self, exposure: ExposureInfo):
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

    def exposure_time_stat_dictionary(self):
        """
        Exposure time stats in a dictionary form.
        Key is the filter name, normalized, value is the cumulative time in seconds.
        """
        result = defaultdict(float)
        for expo in self.exposure_info_list:
            result[expo.filter_name] += expo.exposure_time
        return result


class StatPlotter:
    def __init__(self, plotter_configs: dict = None):
        self.plotter_configs = plotter_configs

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
        for exposure_info in sequence_stat.exposure_info_list:
            hfd_values.append(exposure_info.hfd)
            star_indices.append(exposure_info.star_index)
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
            ax.scatter(focus_index, focus_hfd_value, c=focus_colors, s=1000)

        # hfd and star index
        ax.scatter(img_ids, hfd_values, c=dot_colors, s=500)
        ax.plot(img_ids, hfd_values, color='#FF9800', linewidth=10)
        ax.tick_params(axis='y', labelcolor='#FFB74D')
        ax.set_ylabel('HFD', color='#FFB74D')

        secondary_ax = ax.twinx()
        secondary_ax.scatter(img_ids, star_indices, c=dot_colors, s=500)
        secondary_ax.plot(img_ids, star_indices, color='#9C27B0', linewidth=10)
        secondary_ax.tick_params(axis='y', labelcolor='#BA68C8')
        secondary_ax.set_ylabel('Star Index', color='#BA68C8')

        ax.set_xlabel('Image Index')
        ax.xaxis.label.set_color('#F5F5F5')
        ax.set_title('HFD and StarIndex Plot ({target})'.format(target=target_name))

    def exposure_plot(self, ax: axes.Axes = None, sequence_stat: SequenceStat = None, target_name: str = ''):
        ax.set_facecolor('#212121')
        total_exposure_stat = sequence_stat.exposure_time_stat_dictionary()
        keys = list(total_exposure_stat.keys())
        values = total_exposure_stat.values()
        rectangles = ax.bar(keys, values)
        for i in range(len(keys)):
            filter_name = keys[i]
            if filter_name in self.filter_meta:
                color = self.filter_meta[filter_name]['color']
            else:
                color = '#660874'
            rect = rectangles[i]
            rect.set_color(color)

        x_bound_lower, x_bound_higher = ax.get_xbound()
        ax.set_xbound(x_bound_lower - 0.3, x_bound_higher + 0.3)

        ax.bar_label(rectangles, label_type='center', fontsize=48)

        ax.set_ylabel('Exposure Time(s)')
        ax.yaxis.label.set_color('#F5F5F5')
        ax.set_title('Cumulative Exposure Time by Filter ({target})'.format(target=target_name))

    def guiding_plot(self, ax_main: axes.Axes = None, ax_scatter: axes.Axes = None, sequence_stat: SequenceStat = None,
                     target_name: str = ''):
        config = self.plotter_configs.guiding_error_plot
        ax_main.set_facecolor('#212121')
        ax_main.plot(sequence_stat.guide_x_error_list, color='#F44336', linewidth=2)
        ax_main.plot(sequence_stat.guide_y_error_list, color='#2196F3', linewidth=2)

        abs_x_list = list()
        abs_y_list = list()
        distance_list = list()
        for idx, x_error in enumerate(sequence_stat.guide_x_error_list):
            y_error = sequence_stat.guide_y_error_list[idx]
            abs_x_list.append(abs(x_error))
            abs_y_list.append(abs(y_error))
            distance_list.append(np.sqrt(x_error ** 2 + y_error ** 2))

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
        # ax_scatter.set_xlim([-2.5, 2.5])
        # ax_scatter.set_ylim([-2.5, 2.5])
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

    def plot(self, sequence_stat: SequenceStat = None):
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
        base64_img = base64.b64encode(img_bytes.read())

        # Prevent RuntimeWarning 'More than 20 figures have been opened' from matplotlib
        plt.close('all')

        return base64_img
