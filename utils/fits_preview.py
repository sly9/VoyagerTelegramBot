# import numpy as np
#
# infile = '../image_16.jpg'
# img = cv2.imread(infile, cv2.IMREAD_GRAYSCALE | cv2.IMREAD_ANYDEPTH)
# rgb = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)
# cv2.imwrite('../out.jpg', rgb)
import enum
import os

import cv2
import numpy as np
from astropy.io import fits
from scipy.ndimage import zoom


class ZoomEnum(enum.Enum):
    LARGE = 0.500
    MEDIUM = 0.333
    SMALL = 0.250


class BayerPattern(enum.IntEnum):
    BG = cv2.COLOR_BayerBG2RGB
    BGGR = cv2.COLOR_BayerBGGR2RGB
    GB = cv2.COLOR_BayerGB2RGB
    GBRG = cv2.COLOR_BayerGBRG2RGB
    GR = cv2.COLOR_BayerGR2RGB
    GRBG = cv2.COLOR_BayerGRBG2RGB
    RG = cv2.COLOR_BayerRG2RGB
    RGGB = cv2.COLOR_BayerRGGB2RGB


class FitsRawData:
    def __init__(self, width: int = 1, height: int = 1, bits: int = 1, raw: np.ndarray = np.zeros((1, 1))):
        self.width = width
        self.height = height
        self.bits = bits
        self.raw = raw
        self.owner = ''


class FitsPreview:
    @staticmethod
    def load_fits_data(file_path: str = '') -> FitsRawData or None:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return None

        fits_raw_data = FitsRawData()
        with fits.open(file_path) as hdu_list:
            fits_raw_data.height = hdu_list[0].header['NAXIS1']
            fits_raw_data.width = hdu_list[0].header['NAXIS2']
            fits_raw_data.bits = hdu_list[0].header['BITPIX']
            fits_raw_data.owner = hdu_list[0].header['OBSERVER']

            fits_raw_data.raw = hdu_list[0].data

        return fits_raw_data

    @staticmethod
    def get_valid_output_file_name(original_path: str = '') -> str:
        valid_output_file_name = 'preview.png'

        return valid_output_file_name

    @staticmethod
    def non_linear_stretch(image_data: np.ndarray = np.zeros((1, 1))) -> np.ndarray:
        return image_data

    @staticmethod
    def debayer_with_pattern(image_data: np.ndarray = np.zeros((1, 1)),
                             bayer_pattern: BayerPattern = BayerPattern.RGGB) -> np.ndarray:
        image_data = cv2.cvtColor(image_data, bayer_pattern)
        return image_data

    @staticmethod
    def add_watermark(image_data: np.ndarray = np.zeros((1, 1)), text: str = '') -> np.ndarray:
        watermark = np.zeros(shape=(image_data.shape[0], image_data.shape[1]), dtype=np.uint16)

        cv2.putText(watermark, text=text.strip(), org=(image_data.shape[1] // 16, image_data.shape[0] * 15 // 16),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, color=65535, thickness=8, lineType=cv2.LINE_AA)

        image_data = cv2.addWeighted(src1=image_data, alpha=1, src2=watermark, beta=0.25, gamma=0)

        return image_data

    @staticmethod
    def load_and_process_fits(file_path: str = '', zoom_factor: float = ZoomEnum.LARGE.value,
                              is_color: bool = False, watermark: bool = True) -> np.ndarray:
        if not 0 < zoom_factor < 3.0:
            print('Invalid zoom factor parameter. Use default value(1.0).')
            zoom_factor = 1.0

        fits_image = FitsPreview.load_fits_data(file_path=file_path)
        if fits_image is None:
            return np.zeros((1, 1))
        # Resampling
        resized_image_data = zoom(fits_image.raw, zoom_factor, order=1)
        # Debayering
        if is_color:
            image_data = FitsPreview.debayer_with_pattern(image_data=resized_image_data,
                                                          bayer_pattern=BayerPattern.RGGB)
        else:
            image_data = resized_image_data
        # Stretching
        image_data = FitsPreview.non_linear_stretch(image_data=image_data)
        # Adding watermark
        if watermark:
            image_data = FitsPreview.add_watermark(image_data=image_data, text=fits_image.owner)

        return image_data

    @staticmethod
    def generate_png_preview(file_path: str = '', output_file_path: str = '', zoom_factor: float = ZoomEnum.LARGE.value,
                             is_color: bool = False) -> str or None:
        image_data = FitsPreview.load_and_process_fits(file_path=file_path, zoom_factor=zoom_factor, is_color=is_color)
        file_path = cv2.imwrite(filename=FitsPreview.get_valid_output_file_name(output_file_path), img=image_data)

        return file_path

    @staticmethod
    def generate_jpg_preview(file_path: str = '', output_file_path: str = '', zoom_factor: float = ZoomEnum.LARGE.value,
                             is_color: bool = False, quality: int = 95) -> str:
        if not 0 <= quality <= 100:
            print('Invalid quality parameter. Use default value(95).')
            quality = 95

        image_data = FitsPreview.load_and_process_fits(file_path=file_path, zoom_factor=zoom_factor, is_color=is_color)
        file_path = cv2.imwrite(filename=FitsPreview.get_valid_output_file_name(output_file_path), img=image_data,
                                params=[cv2.IMWRITE_JPEG_QUALITY, quality])

        return file_path


if __name__ == '__main__':
    mono_fits_folder = 'some_folder'
    mono_fits_fn = 'some_file.fit'
    mono_fits_path = os.path.join(mono_fits_folder, mono_fits_fn)
    png_path = FitsPreview.generate_png_preview(file_path=mono_fits_path, zoom_factor=ZoomEnum.LARGE.value,
                                                is_color=False)
