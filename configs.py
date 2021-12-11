import platform
from os.path import exists
import os
import sys
from shutil import copyfile

import yaml


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class ConfigBuilder:
    def __init__(self):
        config_yml_path = os.path.abspath('config.yml')
        config_yml_example_path = resource_path('config.yml.example')
        if not exists(config_yml_path):
            print('!!!!!!!!!!!!!!!!!Config file not set up!!!!!!!!!!!!!!!')
            copyfile(config_yml_example_path, config_yml_path)
            print('''You need a valid configuration file for bot to run. 
I just created a copy of configuration into the same directory as your excutable.
Please open it up with any text editors, and modify at least these sections:
  * telegram_setting
  * voyager_setting
After fixing that, try to open the exe file again. 
            ''')
            if platform.system() == 'Windows':
                os.system('pause')
            else:
                input("Press Enter to exit...")
            sys.exit()

        print('Trying to load these config files: ', config_yml_path, config_yml_example_path)

        with open(config_yml_example_path, 'r') as template_file, open(config_yml_path, 'r') as yaml_f:
            try:
                self.config_yaml = yaml.safe_load(template_file)
                self.config_yaml.update(yaml.safe_load(yaml_f))
            except yaml.YAMLError as exc:
                self.config_yaml = {}
                print(exc)
        print('Configs are loaded: \n', self.config_yaml)
        if 'chat_ids' in self.config_yaml['telegram_setting'] and len(self.config_yaml['telegram_setting']):
            self.config_yaml['telegram_setting']['chat_id'] = self.config_yaml['telegram_setting']['chat_ids'][0]

        self.already_built = False

    def build(self):
        if self.already_built:
            print('This is likely a bug -- building the configuration twice.')
        self.already_built = True
        return class_from_dict('Configs', self.config_yaml.copy())()


def class_from_dict(name: str, dictionary: dict):
    nested_dict = {}
    for k, v in dictionary.items():
        if type(v) == dict:
            nested_dict[k] = v
    for key in nested_dict.keys():
        dictionary.pop(key)

    Class = make_class(classname=name, **dictionary)

    for k, v in nested_dict.items():
        nested_class = make_class(name + '_' + k, **v)
        add_property_to_class(Class, k, nested_class())

    return Class


def property_maker(name):
    storage_name = '_' + name.lower()

    @property
    def prop(self):
        return getattr(self, storage_name)

    @prop.setter
    def prop(self, value):
        setattr(self, storage_name, value)

    return prop


def add_property_to_class(Class, key: str, value):
    storage_name = '_' + key.lower()
    setattr(Class, storage_name, value)
    setattr(Class, key.lower(), property_maker(key))
    return Class


def make_class(classname: str, **options):
    class Class: pass

    Class.__name__ = classname

    for key, value in options.items():
        storage_name = '_' + key.lower()
        setattr(Class, storage_name, value)
        setattr(Class, key.lower(), property_maker(key))

    return Class


if __name__ == "__main__":
    c = ConfigBuilder()
    b = c.build()
    print(b.telegram_setting.chat_id)
    print(b.voyager_setting.domain)
