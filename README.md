# ReefPi macros

## Temp Controlled Fan
Automatically adjust the speed of fans in reef-pi based on a temperature reading.
This uses the reef-pi api to control a reef-pi, whose information is stored in a
config file.

This will automatically control a fan which is setup as a _light_ within reef-pi.
The fact that it's a light doesn't matter, it's just a hack because reef-pi doesn't
have a general purpose power controller, so we pretend it's a 1-channel, manually
controlled light.

For this to function the following settings must be done in the UI:
* create one or more temperatures with their name prefixd with [RPExt][macro=TempFan]
* the temperature must:
    * have its name start with [RPExt][macro=TempFan]
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

```
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
```
