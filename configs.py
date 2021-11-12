import yaml


class ConfigBuilder:
    def __init__(self):
        with open('config.yml', 'r') as yaml_f:
            try:
                self.config_yaml = yaml.safe_load(yaml_f)
            except yaml.YAMLError as exc:
                self.config_yaml = None
                print(exc)
        print('Configs are loaded: \n', self.config_yaml)

    def build(self):
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
    print(b.telegram_setting.chat_ids[0])
    print(b.voyager_setting.domain)
