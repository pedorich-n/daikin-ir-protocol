from daikin_ac_state import DaikinAcMode, DaikinAcState, DaikinFanMode, DaikinSwingMode
from ir_tools import encode_command
from bit_tools import lsb_command_to_msb, reverse_bits, stringify_command

import irgen
import json


ac_modes = {DaikinAcMode.Cool: "cool", DaikinAcMode.Heat: "heat"}
fan_modes = {
    DaikinFanMode.Auto: "auto",
    DaikinFanMode.Quiet: "quiet",
    DaikinFanMode.High: "high",
    DaikinFanMode.MidHigh: "midHigh",
    DaikinFanMode.Mid: "mid",
    DaikinFanMode.LowMid: "lowMid",
    DaikinFanMode.Low: "low",
}
swing_modes = {
    DaikinSwingMode.Auto: "auto",
    DaikinSwingMode.High: "high",
    DaikinSwingMode.MidHigh: "midHigh",
    DaikinSwingMode.Mid: "mid",
    DaikinSwingMode.LowMid: "lowMid",
    DaikinSwingMode.Low: "low",
}


min_temperature = 20
max_temperature = 30


def generate_broadlink_command(state: DaikinAcState) -> str:
    print(state._state)

    command_lsb = state.get_command()
    print(stringify_command(command_lsb, True))

    command_msb = lsb_command_to_msb(command_lsb)
    pulses = encode_command(command_msb)
    broadlink_code = irgen.gen_broadlink_base64_from_raw(pulses)

    return broadlink_code.decode("ascii")


def run(base: dict) -> dict:
    result = base.copy()

    state = DaikinAcState(DaikinAcMode.Off, 25, DaikinFanMode.Auto, DaikinSwingMode.Auto, False, False)
    command = generate_broadlink_command(state)
    result["commands"]["off"] = command

    for ac_mode_enum, ac_mode in ac_modes.items():
        commands_mode = result["commands"].get(ac_mode, None)
        # print(commands_mode)
        if commands_mode is None:
            result["commands"][ac_mode] = {}

        for fan_mode_enum, fan_mode in fan_modes.items():
            commands_fan_mode = result["commands"][ac_mode].get(fan_mode, None)
            # print(commands_fan_mode)
            if commands_fan_mode is None:
                result["commands"][ac_mode][fan_mode] = {}

            for swing_mode_enum, swing_mode in swing_modes.items():
                commands_swing_mode = result["commands"][ac_mode][fan_mode].get(swing_mode, None)
                # print(commands_fan_mode)
                if commands_swing_mode is None:
                    result["commands"][ac_mode][fan_mode][swing_mode] = {}

                for temp in range(min_temperature, max_temperature + 1, 1):
                    if result["commands"][ac_mode][fan_mode][swing_mode].get(str(temp), None) is None:
                        print(f"Learning {ac_mode}, {fan_mode}, {swing_mode}, {temp}C code:")
                        state = DaikinAcState(
                            mode=ac_mode_enum,
                            temperature=temp,
                            fan_mode=fan_mode_enum,
                            swing_mode=swing_mode_enum,
                            no_wind=False,
                            night_mode=False,
                        )
                        command = generate_broadlink_command(state)

                        result["commands"][ac_mode][fan_mode][swing_mode][temp] = command
                    else:
                        print(f"Code for {ac_mode}, {fan_mode}, {temp}C already exists, skipping...")

    return result


if __name__ == "__main__":
    with open("./base.json", "r") as base_file:
        base = json.load(base_file)
        result = run(base)
        with open("./result.json", "w+") as result_file:
            json_object = json.dumps(result, indent=4)
            result_file.write(json_object)
