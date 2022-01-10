from rich import box
from rich.align import Align
from rich.console import RenderResult, ConsoleOptions, Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from data_structure.system_status_info import DitherStatusEnum, GuideStatusEnum, MountStatusEnum, CcdStatusEnum, \
    SpecialDeviceReadingEnum
from destination.rich_console.styles import RichTextStylesEnum


class DeviceStatusPanel:
    """Display header with clock."""

    def __init__(self, config: object, layout: Layout):
        self.system_status_info = None  # type: SystemStatusInfo
        self.layout = layout
        self.config = config
        self.i18n = self.config.i18n.device_status_panel

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height or options.size.height
        yield self.generate_grid(width=width, height=height)

    def generate_grid(self, width: int, height: int):
        status_table = Table.grid(padding=(0, 1))
        status_table.add_column(justify='left')

        device_connection_info = self.system_status_info.device_connection_info
        device_status_info = self.system_status_info.device_status_info
        # CCD
        status_table.add_row('[bold]' + self.i18n['main_camera'] + '[/bold]')
        if device_connection_info.camera_connected:
            ccd_status = device_status_info.ccd_status.status
            ccd_temperature = device_status_info.ccd_status.temperature
            ccd_power_percentage = device_status_info.ccd_status.power_percentage
            if ccd_status == CcdStatusEnum.UNDEF:
                ccd_text = Text(self.i18n['connected'], style=RichTextStylesEnum.SAFE.value)
            elif ccd_status == CcdStatusEnum.TIMEOUT_COOLING or ccd_status == CcdStatusEnum.ERROR:
                ccd_text = Text(ccd_status.name, style=RichTextStylesEnum.CRITICAL.value)
            elif ccd_status == CcdStatusEnum.COOLING or ccd_status == CcdStatusEnum.WARMUP_RUNNING:
                if ccd_temperature == SpecialDeviceReadingEnum.VALUE_DEVICE_OFF:
                    ccd_text = Text(CcdStatusEnum.OFF.name, style=RichTextStylesEnum.CRITICAL.value)
                elif ccd_temperature == SpecialDeviceReadingEnum.VALUE_ERROR:
                    ccd_text = Text(CcdStatusEnum.ERROR.name, style=RichTextStylesEnum.CRITICAL.value)
                else:
                    ccd_text = Text(f'{ccd_temperature}°C | {ccd_status.name}', style=RichTextStylesEnum.WARNING.value)
            elif ccd_status == CcdStatusEnum.COOLED or ccd_status == CcdStatusEnum.WARMUP_END:
                if ccd_temperature == SpecialDeviceReadingEnum.VALUE_DEVICE_OFF:
                    ccd_text = Text(CcdStatusEnum.OFF.name, style=RichTextStylesEnum.CRITICAL.value)
                elif ccd_temperature == SpecialDeviceReadingEnum.VALUE_ERROR:
                    ccd_text = Text(CcdStatusEnum.ERROR.name, style=RichTextStylesEnum.CRITICAL.value)
                else:
                    ccd_text = Text(f'{ccd_temperature}°C | {ccd_power_percentage} %',
                                    style=RichTextStylesEnum.SAFE.value)
            else:
                # CcdStatEnum.INIT, NO_COOLER, or OFF:
                ccd_text = Text(ccd_status.name, style=RichTextStylesEnum.SAFE.value)
        else:
            ccd_text = Text(self.i18n['disconnected'],
                            style=(RichTextStylesEnum.CRITICAL.value + ' blink'))

        status_table.add_row(ccd_text)

        if height > 22:
            status_table.add_row(end_section=True)

        # Mount
        status_table.add_row(self.i18n['mount'])
        if device_connection_info.mount_connected:
            mount_status = device_status_info.mount_status
            if mount_status == MountStatusEnum.TRACKING:
                mount_text = Text(mount_status.name, style=RichTextStylesEnum.SAFE.value)
            elif mount_status == MountStatusEnum.PARKED:
                mount_text = Text(mount_status.name, style=RichTextStylesEnum.CRITICAL.value)
            elif mount_status == MountStatusEnum.SLEWING:
                mount_text = Text(mount_status.name, style=RichTextStylesEnum.WARNING.value)
            else:
                # MountOperationEnum.UNDEF and invalid values
                mount_text = Text(self.i18n['connected'],
                                  style=RichTextStylesEnum.SAFE.value)
        else:
            mount_text = Text(self.i18n['disconnected'],
                              style=(RichTextStylesEnum.CRITICAL.value + ' blink'))

        status_table.add_row(mount_text)

        if height > 22:
            status_table.add_row(end_section=True)

        # Auto Focuser
        if device_connection_info.focuser_connected:
            status_table.add_row(self.i18n['focuser'])
            focuser_status = device_status_info.focuser_status

            if focuser_status.temperature == SpecialDeviceReadingEnum.VALUE_DEVICE_OFF:
                focuser_text = Text('OFF', style=RichTextStylesEnum.CRITICAL.value)
            elif focuser_status.temperature == SpecialDeviceReadingEnum.VALUE_ERROR:
                focuser_text = Text('ERROR', style=RichTextStylesEnum.CRITICAL.value)
            else:
                focuser_text = Text(f'{focuser_status.temperature}°C | {focuser_status.position}',
                                    style=RichTextStylesEnum.SAFE.value)

            status_table.add_row(focuser_text)

        if height > 22:
            status_table.add_row(end_section=True)

        # Rotator
        if device_connection_info.rotator_connected:
            status_table.add_row(self.i18n['rotator'])
            rotator_status = device_status_info.rotator_status
            if rotator_status.is_rotating:
                status_table.add_row(Text('ROTATING', style=RichTextStylesEnum.WARNING.value))
            status_table.add_row(f'Sky PA: {rotator_status.sky_pa}°')
            status_table.add_row(f'Rotator PA: {rotator_status.rotator_pa}°')
        if height > 22:
            status_table.add_row(end_section=True)

        # Guiding
        status_table.add_row(self.i18n['guiding'])
        if device_status_info.guide_status == GuideStatusEnum.RUNNING:
            guide_text = Text('ON', style=RichTextStylesEnum.SAFE.value)
        else:
            guide_text = Text('OFF', style=RichTextStylesEnum.CRITICAL.value)
        status_table.add_row(guide_text)
        if height > 22:
            status_table.add_row(end_section=True)
        # Dithering
        status_table.add_row(self.i18n['dithering'])
        if device_status_info.dither_status == DitherStatusEnum.RUNNING or \
                device_status_info.dither_status == DitherStatusEnum.WAITING_SETTLE:
            dither_text = Text(device_status_info.dither_status.name, style=RichTextStylesEnum.SAFE.value)
        elif device_status_info.dither_status == DitherStatusEnum.STOPPED:
            dither_text = Text(device_status_info.dither_status.name)
        else:
            dither_text = Text(device_status_info.dither_status.name, style=RichTextStylesEnum.CRITICAL.value)

        status_table.add_row(dither_text)

        status_panel = Panel(
            Align.center(status_table, vertical='top'),
            box=box.ROUNDED,
            padding=(1, 2),
            title="[b blue]" + self.i18n['panel_name'],
            border_style='bright_blue',
        )

        return status_panel
