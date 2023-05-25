import os
import yaml
import logging
import logging.config



ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT_DIR,'logging.yml'), "r") as file:
  try:
    config=yaml.safe_load(file)
    logging.config.dictConfig(config)
  except yaml.YAMLError as e:
    raise("Error while parsing YAML config file")