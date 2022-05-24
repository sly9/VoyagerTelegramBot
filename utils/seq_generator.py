import os
from collections import OrderedDict

import xmltodict
from dicttoxml import dicttoxml

ITEM_LOCATOR = {
    'TARGET_ARRAY': 'ref-3',
    'TARGET_NAME': 'ref-146',
    'TARGET_RA': 'ref-142',
    'TARGET_DEC': 'ref-144',
    'GAIN_OFFSET_ARRAY_LIST': 'ref-141',
    'GAIN_OFFSET_ARRAY': 'ref-148',
    'IMAGE_SLOT_ARRAY_LIST': 'ref-143',
    'IMAGE_SLOT_ARRAY': 'ref-149',
}

A3_SCHEMA = 'http://schemas.microsoft.com/clr/nsassem/Voyager2/Voyager2%2C%20Version%3D1.0.0.0%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3Dnull'
START_IDX = 150

# Personalized dict2xml parser since dicttoxml cannot parse xmltodict object
def dict2xml(d, root_node=None):
    wrap = False if None == root_node or isinstance(d, list) else True
    root = 'objects' if None == root_node else root_node
    root_singular = root[:-1] if 's' == root[-1] and None == root_node else root
    xml = ''
    attr = ''
    children = []

    if isinstance(d, dict):
        for key, value in dict.items(d):
            if isinstance(value, dict):
                children.append(dict2xml(value, key))
            elif isinstance(value, list):
                children.append(dict2xml(value, key))
            elif key[0] == '@':
                # attributes
                attr = attr + ' ' + key[1::] + '="' + str(value) + '"'
            elif key == '#text':
                # text
                xml = str(value)
                children.append(xml)
            else:
                xml = '<' + key + ">" + str(value) + '</' + key + '>'
                children.append(xml)

    else:
        # if list
        for value in d:
            children.append(dict2xml(value, root_singular))

    end_tag = '>' if 0 < len(children) else '/>'

    if wrap or isinstance(d, dict):
        xml = '<' + root + attr + end_tag

    if 0 < len(children):
        for child in children:
            xml = xml + child

        if wrap or isinstance(d, dict):
            xml = xml + '</' + root + '>'

    return xml

class GainOffset:
    def __init__(self, gain: int = 100, offset: int = 10):
        self.gain = gain
        self.offset = offset


class ImageSlot:
    def __init__(self, exposure: float = 1.0, binning: int = 1, count: int = 1, filter_idx: int = 0,
                 gain_offset: GainOffset = GainOffset(gain=0, offset=0)):
        self.exposure = exposure
        self.binning = binning
        self.count = count
        self.filter_idx = filter_idx
        self.gain_offset = gain_offset


class AstroTarget:
    def __init__(self, target_name: str = 'TargetHolder', ra: str = '00 00 00.000', dec: str = '000 00 00.00'):
        self.name = target_name
        self.ra = ra
        self.dec = dec
        self.image_slots = list()
        self.slot_counter = 0

    def append_slot(self, image_slot: ImageSlot):
        self.image_slots.append(image_slot)
        self.slot_counter += 1


class VoyagerSequenceGenerator:
    def __init__(self, base_seq_path: str = ''):
        if not os.path.exists(base_seq_path) or not os.path.isfile(base_seq_path):
            raise FileNotFoundError

        self.base_seq_path = base_seq_path
        self.target = None
        self.sequence_obj = None

    def set_target(self, target: AstroTarget or None):
        if target is None:
            return

        self.target = target

    def generate_seq(self):
        if self.target is None:
            return

        sequence_content = None
        with open(self.base_seq_path, 'r') as base_sequence_f:
            base_sequence_content = base_sequence_f.read()
            sequence_content = xmltodict.parse(base_sequence_content)

        if sequence_content is None:
            return

        ref_idx = START_IDX
        array_objs = sequence_content['SOAP-ENV:Envelope']['SOAP-ENV:Body']['SOAP-ENC:Array']
        for array_obj in array_objs:
            if '@id' in array_obj:
                if array_obj['@id'] == ITEM_LOCATOR['TARGET_ARRAY']:
                    # Object that contains target information
                    for item in array_obj['item']:
                        if '@id' in item:
                            if item['@id'] == ITEM_LOCATOR['TARGET_NAME']:
                                item['#text'] = self.target.name
                            if item['@id'] == ITEM_LOCATOR['TARGET_RA']:
                                item['#text'] = self.target.ra
                            if item['@id'] == ITEM_LOCATOR['TARGET_DEC']:
                                item['#text'] = self.target.dec

                if array_obj['@id'] == ITEM_LOCATOR['GAIN_OFFSET_ARRAY']:
                    # Object that contains gain/offset reference
                    gain_offset_list = list()

                    for _ in range(self.target.slot_counter):
                        ref_idx_str = '#ref-{}'.format(ref_idx)
                        ref_dict = OrderedDict([('@href', ref_idx_str)])
                        gain_offset_list.append(ref_dict)
                        ref_idx += 1

                    array_obj['item'] = gain_offset_list

                if array_obj['@id'] == ITEM_LOCATOR['IMAGE_SLOT_ARRAY']:
                    # Object that contains image slots reference
                    image_slots_list = list()

                    for _ in range(self.target.slot_counter):
                        ref_idx_str = '#ref-{}'.format(ref_idx)
                        ref_dict = OrderedDict([('@href', ref_idx_str)])
                        image_slots_list.append(ref_dict)
                        ref_idx += 1

                    array_obj['item'] = image_slots_list

        # Reference array lists
        a1_array_objs = sequence_content['SOAP-ENV:Envelope']['SOAP-ENV:Body']['a1:ArrayList']
        for a1_array_obj in a1_array_objs:
            if '@id' in a1_array_obj:
                if a1_array_obj['@id'] == ITEM_LOCATOR['GAIN_OFFSET_ARRAY_LIST'] or \
                        a1_array_obj['@id'] == ITEM_LOCATOR['IMAGE_SLOT_ARRAY_LIST']:
                    a1_array_obj['_size'] = self.target.slot_counter

        ref_idx = START_IDX
        gain_offset_list = list()
        image_slots_list = list()
        for idx, image_slot in enumerate(self.target.image_slots):
            # Add gain/offset item
            ref_idx_str = 'ref-{}'.format(ref_idx + idx)
            gain_offset_obj = OrderedDict([('@id', ref_idx_str),
                                           ('@xmlns:a3', A3_SCHEMA),
                                           ('SlotNumber', idx + 1),
                                           ('Gain', image_slot.gain_offset.gain),
                                           ('Offset', image_slot.gain_offset.offset)])
            gain_offset_list.append(gain_offset_obj)
            # Add image slot
            ref_idx_str = 'ref-{}'.format(ref_idx + idx + self.target.slot_counter)
            image_slot_obj = OrderedDict([('@id', ref_idx_str),
                                          ('@xmlns:a3', A3_SCHEMA),
                                          ('mTipoEsposizione', 0),
                                          ('mFiltroIndice', image_slot.filter_idx),
                                          ('mFiltroLabel', OrderedDict([('@href', '#ref-140')])),
                                          ('mEsposizioneSecondi', image_slot.exposure),
                                          ('mBinning', image_slot.binning),
                                          ('mNumero', image_slot.count),
                                          ('mSpeedIndice', 0),
                                          ('mReadoutIndice', 0),
                                          ('mPlanningHelpElaborate', 0),
                                          ('mEseguite', 0),
                                          ('mStatisticheSub', OrderedDict([('@xsi:null', '1')])),
                                          ('mLastInsNum', 0)])
            image_slots_list.append(image_slot_obj)

        sequence_content['SOAP-ENV:Envelope']['SOAP-ENV:Body']['a3:SequenzaElementoGainOffset'] = gain_offset_list
        sequence_content['SOAP-ENV:Envelope']['SOAP-ENV:Body']['a3:SequenzaElemento'] = image_slots_list

        self.sequence_obj = sequence_content

    def generate_seq_with_target(self, target: AstroTarget or None):
        self.set_target(target=target)
        self.generate_seq()

    def write_seq_to_file(self, file_path: str = ''):
        print(self.sequence_obj)
        with open(file_path, 'w') as output_f:
            xml_obj = dict2xml(self.sequence_obj)[9:-10]
            output_f.write(xml_obj)
        pass


if __name__ == '__main__':
    sequence_target = AstroTarget(target_name='M42', ra='05 35 17.300', dec='-05 23 28.00')
    narrowband_gain_offset = GainOffset(gain=100, offset=10)
    wideband_gain_offset = GainOffset(gain=10, offset=10)

    image_slot = ImageSlot(exposure=1, binning=1, count=1, filter_idx=0, gain_offset=narrowband_gain_offset)
    sequence_target.append_slot(image_slot)

    image_slot = ImageSlot(exposure=2, binning=2, count=2, filter_idx=1, gain_offset=narrowband_gain_offset)
    sequence_target.append_slot(image_slot)

    image_slot = ImageSlot(exposure=3, binning=3, count=3, filter_idx=2, gain_offset=wideband_gain_offset)
    sequence_target.append_slot(image_slot)

    seq_generator = VoyagerSequenceGenerator(base_seq_path='path_to_base.s2q')
    seq_generator.generate_seq_with_target(target=sequence_target)
    seq_generator.write_seq_to_file(file_path='path_to_generated.s2q')
