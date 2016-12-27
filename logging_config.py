import logging
import logging.handlers
import os
import sys

import requests
requests.packages.urllib3.disable_warnings()
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("requests").addHandler(logging.NullHandler())

parent_folder = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"

file_logger = logging.getLogger("my_file_logger")
file_logger.setLevel(logging.DEBUG)
file_logger.propagate = 0

file_formatter = logging.Formatter("%(asctime)s\t%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler = logging.handlers.TimedRotatingFileHandler(parent_folder + "logs/TndrAssistant.log", when="midnight", backupCount=6)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)
file_logger.addHandler(file_handler)

console_logger = logging.getLogger("my_console_logger")
console_logger.setLevel(logging.DEBUG)
console_logger.propagate = 0
console_formatter = logging.Formatter("%(asctime)s\t%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
console_logger.addHandler(console_handler)