import os
from configparser import ConfigParser
from sqlalchemy.engine.url import make_url
from .model import SessionManager

MY_PATH = os.path.dirname(__file__)
config_path = os.path.join(MY_PATH, '..', "config.ini")

config = ConfigParser()
config.read(config_path)

_url = config['DATABASE']['url']
db_session = SessionManager.session(make_url(_url))

def blank_string(val):
	return (val == None) or (str(val).rstrip() == '')

def blank_value(val):
	return (val == {}) or (val == []) or (blank_string(val))
