import json
import os
from typing import List

import irgen

from src.bit_tools import lsb_command_to_msb, reverse_bits, stringify_command
from src.daikin_ac_state import (DaikinAcMode, DaikinAcState, DaikinFanMode,
                                 DaikinSwingMode)
from src.ir_tools import encode_command

ac_modes_to_string = {
    DaikinAcMode.Cool: "cool",
    DaikinAcMode.Heat: "heat",
    DaikinAcMode.Dry: "dry",
    DaikinAcMode.Fan: "fan_only",
}
ac_modes_from_string = {v: k for k, v in ac_modes_to_string.items()}

fan_modes_to_string = {
    DaikinFanMode.Auto: "auto",
    DaikinFanMode.Quiet: "quiet",
    DaikinFanMode.High: "high",
    DaikinFanMode.MidHigh: "midHigh",
    DaikinFanMode.Mid: "mid",
    DaikinFanMode.LowMid: "midLow",
    DaikinFanMode.Low: "low",
}
fan_modes_from_string = {v: k for k, v in fan_modes_to_string.items()}

swing_modes_to_string = {
    DaikinSwingMode.Auto: "auto",
    DaikinSwingMode.High: "high",
    DaikinSwingMode.MidHigh: "midHigh",
    DaikinSwingMode.Mid: "mid",
    DaikinSwingMode.LowMid: "midLow",
    DaikinSwingMode.Low: "low",
}
swing_modes_from_string = {v: k for k, v in swing_modes_to_string.items()}



def generate_broadlink_command(state: DaikinAcState) -> str:
    # print(state._state)

    command_lsb = state.get_command()
    # print(stringify_command(command_lsb, True))

    command_msb = lsb_command_to_msb(command_lsb)
    pulses = encode_command(command_msb)
    broadlink_code = irgen.gen_broadlink_base64_from_raw(pulses)

    return broadlink_code.decode("ascii")


def run(base: dict) -> dict:
    ac_modes: List[DaikinAcMode] = [ac_modes_from_string[mode] for mode in base["operationModes"]]
    fan_modes: List[DaikinFanMode] = [fan_modes_from_string[mode] for mode in base["fanModes"]]
    swing_modes: List[DaikinSwingMode] = [swing_modes_from_string[mode] for mode in base["swingModes"]]
    min_temperature = int(base["minTemperature"])
    max_temperature = int(base["maxTemperature"])

    result = base.copy()

    state = DaikinAcState(DaikinAcMode.Off, 25, DaikinFanMode.Auto, DaikinSwingMode.Auto, False, False)
    command = generate_broadlink_command(state)
    result["commands"]["off"] = command

    for ac_mode in ac_modes:
        ac_mode_str = ac_modes_to_string[ac_mode]
        commands_mode = result["commands"].get(ac_mode_str, None)
        # print(commands_mode)
        if commands_mode is None:
            result["commands"][ac_mode_str] = {}

        for fan_mode in fan_modes:
            fan_mode_str = fan_modes_to_string[fan_mode]
            commands_fan_mode = result["commands"][ac_mode_str].get(fan_mode_str, None)
            # print(commands_fan_mode)
            if commands_fan_mode is None:
                result["commands"][ac_mode_str][fan_mode_str] = {}

            for swing_mode in swing_modes:
                swing_mode_str = swing_modes_to_string[swing_mode]
                commands_swing_mode = result["commands"][ac_mode_str][fan_mode_str].get(swing_mode_str, None)
                # print(commands_fan_mode)
                if commands_swing_mode is None:
                    result["commands"][ac_mode_str][fan_mode_str][swing_mode_str] = {}

                for temp in range(min_temperature, max_temperature + 1, 1):
                    if result["commands"][ac_mode_str][fan_mode_str][swing_mode_str].get(str(temp), None) is None:
                        state = DaikinAcState(
                            mode=ac_mode,
                            temperature=temp,
                            fan_mode=fan_mode,
                            swing_mode=swing_mode,
                            no_wind=False,
                            night_mode=False,
                        )
                        prefix = f"Writing {ac_mode_str}, {fan_mode_str}, {swing_mode_str}, {temp}C code:".ljust(48, " ")
                        command_str = stringify_command(state.get_command(), True)
                        print(f"{prefix}{command_str}")

                        command = generate_broadlink_command(state)
                        result["commands"][ac_mode_str][fan_mode_str][swing_mode_str][temp] = command
                    else:
                        print(f"Code for {ac_mode_str}, {fan_mode_str}, {swing_mode_str}, {temp}C already exists, skipping...")

    return result

def main():
    # TODO: do not hardcode paths
    base_path = os.path.join(os.path.dirname(__file__), "base.json")
    result_path = os.path.join(os.path.dirname(__file__), "result.json")

    with open(base_path, "r") as base_file:
        base = json.load(base_file)
        result = run(base)
        with open(result_path, "w+") as result_file:
            json_object = json.dumps(result, indent=4)
            result_file.write(json_object)


if __name__ == '__main__':
    main()