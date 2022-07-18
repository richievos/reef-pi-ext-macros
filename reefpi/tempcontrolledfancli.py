#!/usr/bin/env python

TEMP_PREFIX = "[RPExt][macro=TempFan]"

DESCRIPTION = f"""
Automatically adjust the speed of fans in reef-pi based on a temperature reading.
This uses the reef-pi api to control a reef-pi, whose information is stored in a
config file.

This will automatically control a fan which is setup as a _light_ within reef-pi.
The fact that it's a light doesn't matter, it's just a hack because reef-pi doesn't
have a general purpose power controller, so we pretend it's a 1-channel, manually
controlled light.

For this to function the following settings must be done in the UI:
* create one or more temperatures with their name prefixd with {TEMP_PREFIX}
* the temperature must:
    * have its name start with {TEMP_PREFIX}
    * be enabled
    * be setup to control a macro as a chiller
    * have the chiller's temperature set to something
* the macro that the temperature is attached to:
    * must have one or more "lights" attached to it (which are really fans)
    * should not be reversible, just to avoid reef-pi disabling it (doesn't really matter though)

The temperature will be adjusted based on:
    * fan speed 0 = temperature's cooler temp (temp["max"])
    * fan speed 100 = speed 0 + the relevant fan_temp_max in the config (F or C)

While this script can be run anywhere that has access to the reef-pi, the safest
setup is to run this from within the reef-pi device itself as a cron job. For that
you just run with `"hostname": "localhost"` in the configs, and you'd likely run
the cron job every minute.

Instructions:

# Retrieve the macros repo
$ git clone https://github.com/richievos/reef-pi-ext-macros.git
$ cd reef-pi-ext-macros

# Setup your machine for the macro scripts
$ pip install -r requirements.txt

# Setup your config file
$ cp config.json.example config.json
# EDIT config.json as appropriate

# Do a trial-run
$ python reefpi/tempcontrolledfancli.py --config-file=./config.json

# Run the scripts automatically with cron
$ crontab -e
# Your settings should look like:
* * * * * /home/pi/reef-pi-ext-macros/reefpi/tempcontrolledfancli.py  --config-file=/home/pi/reef-pi-ext-macros/reefpi/config.json

"""

import argparse
import json
from os import path
import sys


def _read_configs(config_file):
    return json.loads(cf.read())


def dir_path(p):
    if path.isdir(p):
        return p
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{p} is not a valid path")


parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--config-file', dest='config_file', type=argparse.FileType('r'),
                    required=True,
                    help='config file with settings')
parser.add_argument('--metric-output-folder', dest='metric_output_folder', type=dir_path,
                    help='folder to output readings to (defaults to being read from the config file)')


if __name__ == '__main__':
    sys.path.append(path.abspath(str(sys.modules['__main__'].__file__) + "/../.."))

    from reefpi.client import ReefPiClient
    import reefpi.tempcontrolledfan as tempcontrolledfan


    args = parser.parse_args()

    with args.config_file as cf:
        config = _read_configs(cf)

    client = ReefPiClient(config["hostname"])
    credentials = config["credentials"]
    client.login_and_set_session(credentials["username"], credentials["password"])

    metric_output_folder = args.metric_output_folder or config.get("metric_output_folder", None)

    tempcontrolledfan.update_fans(client, fan_temp_max=config["fan_temp_max"], temp_prefix=TEMP_PREFIX, metric_output_folder=metric_output_folder)
