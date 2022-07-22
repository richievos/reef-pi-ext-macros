#!/usr/bin/env python

import os

############################################################
# Example light data:
# {"id":"7","name":"DC 4 fan",
#  "channels":{"4":{"name":"Channel-1","min":0,"max":100,"pin":4,"color":"#000000","manual":true,
#                     "value":100,"profile":{"type":"fixed","config":{"start":"00:00:00","end":"23:59:59","value":0},
#                     "min":0,"max":0}}},
#  "jack":"1","enable":true}
def _update_light_value_from_range(light, cur_frac):
    def _update_chan(channel):
        range = channel["max"] - channel["min"]
        channel["value"] = min(round(channel["min"] + cur_frac * range), channel["max"])
        return channel

    channels = {id: _update_chan(chan) for id, chan in light["channels"].items()}

    return {**light, **{ "channels": channels}}


def _calc_frac_of_temp_range(fan_config, cur):
    """ Given min=10, max=100, cur=20 then frac=2/9 = 0.222 """

    range = fan_config["fan_max"] - fan_config["fan_min"]
    frac = (cur - fan_config["fan_min"]) / range
    # bound to [0, 1]
    frac = max(0.0, frac)
    frac = min(1.0, frac)

    return frac


def _index_by_id(lst):
    return { el["id"]: el for el in lst }


def _get_controlled_temps(client, temp_prefix):
    temps = client.get_temps()
    possible_controlled_temps = [temp for temp in temps if temp["enable"] and temp["control"] and temp["is_macro"]]

    controlled_temps = [temp for temp in possible_controlled_temps if temp["name"].startswith(temp_prefix)]

    print("Found {controlled} controlled_temps from {total} temps which were enabled and macros".format(total=len(possible_controlled_temps), controlled=len(controlled_temps)))
    return controlled_temps


def _get_fan_config(temp, fan_temp_max):
    min_fan_temp = temp["max"]
    if temp["fahrenheit"]:
        max_fan_temp = min_fan_temp + fan_temp_max["F"]
    else:
        max_fan_temp = min_fan_temp + fan_temp_max["C"]
    return { "fan_min": min_fan_temp, "fan_max": max_fan_temp }


def _get_lights_from_macro(macro_for_temp, lights):
    """ Given a macro, extract the lights from the steps """

    # {'id': '5', 'name': '[RPExt][macro=TempFan] DC4', 'steps': [{'type': 'lightings', 'config': {'duration': '', 'title': '', 'message': '', 'on': True, 'id': '7'}}], 'reversible': False}
    lighting_steps = [step for step in macro_for_temp["steps"] if step["type"] == "lightings"]
    light_ids = [step["config"]["id"] for step in lighting_steps]
    return {k: lights[k] for k in light_ids}


def _write_frac_to_metric_output_folder(temp, metric_output_folder, temp_frac):
    temp_id = temp["id"]
    with open(os.path.join(metric_output_folder, f"varfan-temp-{temp_id}"), "w") as f:
        f.write(str(temp_frac))


def update_fans(client, fan_temp_max, fan_speed_min, temp_prefix, metric_output_folder):
    """ Set the appropriate fan speed for temp controlled fans """

    lights = _index_by_id(client.get_lights())
    macros = _index_by_id(client.get_macros())

    fan_speed_min_frac = fan_speed_min / 100.0

    controlled_temps = _get_controlled_temps(client, temp_prefix)
    for temp in controlled_temps:
        macro_for_temp = macros[temp["cooler"]]

        fan_config = _get_fan_config(temp, fan_temp_max)

        # TODO: warning after editing a temperature it appears its current_reading
        #       temporarily resets to 0. That'll cause a momentary blip whenever
        #       a fan gets edited
        cur_reading = client.get_current_reading(temp["id"])

        temp_frac = _calc_frac_of_temp_range(fan_config, cur=cur_reading["temperature"])
        if temp_frac < fan_speed_min_frac:
            temp_frac = 0.0

        if metric_output_folder:
            _write_frac_to_metric_output_folder(temp, metric_output_folder, temp_frac)

        lights = _get_lights_from_macro(macro_for_temp, lights)

        for light_id, light in lights.items():
            updated_light = _update_light_value_from_range(light=light, cur_frac=temp_frac)
            # Just to make sure it gets flipped on
            updated_light = {**updated_light, **{"enabled": True}}

            print("Setting fan({light_id}, \"{fan_name}\") speed to {temp_frac} due to cur_reading={cur_reading} for \"{temp_name}\" ({temp_id})".format(
                light_id=light_id, fan_name=light["name"], temp_frac=round(temp_frac*100), cur_reading=cur_reading["temperature"], temp_name=temp["name"], temp_id=temp["id"]))
            client.update_light(updated_light)
