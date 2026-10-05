import logging
import json
import os

def get_config():
    logging.debug("Trying to read config file")
    if os.path.exists(os.environ['OCP_CONFIG_FILE']):
        with open(os.environ['OCP_CONFIG_FILE'], 'r') as f:
            config = json.load(f)
            return config
    else:
        raise Exception("No configuration file found")

def assert_this(*arg):
    black_list = ['paas', 'prod', 'dmz', 'openshift', 'trident', 'kube']

    for i in arg: assert i in black_list