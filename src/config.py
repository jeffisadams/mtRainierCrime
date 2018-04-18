import os
from configparser import ConfigParser


def main():
  # Config Init
  config = ConfigParser()
  if "PYTHON_ENV" in os.environ:
    config.read('config/{0}.ini'.format(os.environ['PYTHON_ENV']))
  else:
    config.read('config/default.ini')
  return config

