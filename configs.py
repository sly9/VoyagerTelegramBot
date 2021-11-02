import yaml


class Configs:
    def __init__(self):
        with open('config.yml', 'r') as yaml_f:
            try:
                self.configs = yaml.safe_load(yaml_f)
            except yaml.YAMLError as exc:
                self.configs = None
                print(exc)

        print('Configs are loaded: \n', self.configs)
