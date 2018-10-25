# *-* encoding=utf-8 *-*
import os
from configparser import RawConfigParser
import glob


class RuleLoader:
    def __init__(self, conf_path):
        for item in glob.glob(os.path.join(conf_path, "*.conf")):
            self.cp = RawConfigParser()
            self.cp.read(item)

    def get_rules(self, data_type):
        return self.cp.items(data_type)

    def get_option(self, data_type, key):
        return self.cp.get(data_type, key)
