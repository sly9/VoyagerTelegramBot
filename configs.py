import os
import platform
import sys
from os.path import exists
from shutil import copyfile

import pyaml
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
    def __init__(self, config_filename: str = 'config.yml'):
        self.already_built = False
        self.config_filename = config_filename

        self.config_yaml = None

    def validate(self):
        config_yml_path = os.path.abspath(self.config_filename)
        config_yml_example_path = resource_path('config.yml.example')
        if not exists(config_yml_path):
            print('!!!!!!!!!!!!!!!!!Config file not set up!!!!!!!!!!!!!!!')
            print('''You need a valid configuration file for bot to run. 
        I just created a copy of configuration into the same directory as your executable.
        Please open it up with any text editors, and modify at least these sections:
          * telegram_setting
          * voyager_setting
        After fixing that, try to open the exe file again. 
                    ''')
            if platform.system() == 'Windows':
                os.system('pause')
            else:
                input("Press Enter to exit...")
            return 'NO_CONFIG_FILE'

        print('Trying to load these config files: ', config_yml_path, config_yml_example_path)

        with open(config_yml_example_path, 'r') as template_file, open(config_yml_path, 'r') as yaml_f:
            try:
                config_yaml = yaml.safe_load(yaml_f)
                config_yaml_template = yaml.safe_load(template_file)
                if 'config_template_version' not in config_yaml or config_yaml_template['config_template_version'] != \
                        config_yaml['config_template_version']:
                    return 'TEMPLATE_VERSION_DIFFERENCE'
                self.config_yaml = config_yaml_template

                self.config_yaml.update(config_yaml)
            except Exception as exc:
                print(exc)
                return 'LOAD_CONFIG_FAILED'

        if 'chat_ids' in self.config_yaml['telegram_setting'] and len(self.config_yaml['telegram_setting']):
            self.config_yaml['telegram_setting']['chat_id'] = self.config_yaml['telegram_setting']['chat_ids'][0]

        config_for_printing = self.config_yaml.copy()
        config_for_printing.pop('telegram_setting')
        config_for_printing.pop('voyager_setting')

        print('Loaded configuration:\n')
        print('<== Credentials for telegram and Voyager are hidden ==>')
        pyaml.p(config_for_printing)
        print('<=====================================================>')
        return 0

    def merge(self):
        config_yml_path = os.path.abspath(self.config_filename)
        config_yml_example_path = resource_path('config.yml.example')
        with open(config_yml_example_path, 'r') as template_file, open(config_yml_path, 'r') as yaml_f:
            try:
                config_yaml = yaml.safe_load(yaml_f)
                config_yaml_template = yaml.safe_load(template_file)

                config_yaml_template['voyager_setting'] = config_yaml['voyager_setting']
                config_yaml_template['telegram_setting'] = config_yaml['telegram_setting']

                self.config_yaml = config_yaml_template
            except Exception as exc:
                print(exc)
                raise 'MERGE_CONFIG_FAILED'
        with open(config_yml_path,'w') as yaml_file:
            yaml.safe_dump(self.config_yaml,yaml_file)

    def copy_template(self):
        config_yml_path = os.path.abspath(self.config_filename)
        config_yml_example_path = resource_path('config.yml.example')
        copyfile(config_yml_example_path, config_yml_path)

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
