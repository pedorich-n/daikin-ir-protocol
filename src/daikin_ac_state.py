import struct
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, IntEnum, IntFlag, auto
from functools import partial, reduce
from typing import Dict, List, Optional

from src.tools import find_first, if_not_none, is_not_none_and


################################################## Public Enums ##################################################
class DaikinAcMode(Enum):
    Heat = auto()
    Cool = auto()
    Dry = auto()
    Fan = auto()
    Auto = auto()
    Off = auto()


class DaikinFanMode(Enum):
    Auto = auto()
    Quiet = auto()
    Low = auto()
    LowMid = auto()
    Mid = auto()
    MidHigh = auto()
    High = auto()


class DaikinSwingMode(Enum):
    Auto = auto()
    Low = auto()
    LowMid = auto()
    Mid = auto()
    MidHigh = auto()
    High = auto()


@dataclass
class DaikinAcStateHolder:
    mode: DaikinAcMode
    temperature: int
    fan_mode: DaikinFanMode
    swing_mode: DaikinSwingMode
    no_wind: bool = False
    night_mode: bool = False
    on_timer_hours: Optional[int] = None
    off_timer_hours: Optional[int] = None


class DaikinAcButtons(IntFlag):
    Off = 0x02
    Temperature = 0x03
    Swing = 0x06
    Fan = 0x07
    NoWind = 0x34
    ModeHeat = 0x10
    ModeCool = 0x0E
    ModeAuto = 0x0D
    ModeDry = 0x0F
    ModeFan = 0x1A


# Enum represents information position in the array starting from 0
class DaikinCommandOffset(IntEnum):
    Button = 9
    OffMarker = 11  # Not sure what this value is for, but only time it's different from 0x00 is when Off button is pressed
    SwingMode = 12
    Stream = 14
    Frame1Checksum = 19
    Mode = 25
    Temperature = 26
    TemperatureMode = 27  # Used for Auto and Dry modes for some reason
    FanSwingMode = 28
    Timer1 = 30
    Timer2 = 31
    Timer3 = 32
    NightMode = 33
    NoWind = 36
    Frame2Checksum = 38


@dataclass
class HexValue:
    value: int
    offset: int

    def __str__(self) -> str:
        return f"HexValue(value={hex(self.value)}, offset={self.offset})"


################################################## Private static values ##################################################
# Example: [11 DA 27 00 02 00 00 00 00 0C 00 00 00 00 00 00 00 00 00 20 | 11 DA 27 00 00 49 32 00 AF 00 00 06 60 00 00 C3 00 00 65]
# All 0xFF are placeholders
#                                                                          Button      OffM  Swing                                     Checksum
_frame_1_template = [0x11, 0xDA, 0x27, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF]
#                                                  Mode  Temp  TempM F/S         Timers (3 byte)   Night             NoWind      Checksum
_frame_2_template = [0x11, 0xDA, 0x27, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0xC3, 0xFF, 0x00, 0xFF]

_button_partial = partial(HexValue, offset=DaikinCommandOffset.Button.value)
_fan_swing_mode_partial = partial(HexValue, offset=DaikinCommandOffset.FanSwingMode.value)

_default_off_command = HexValue(0x38, DaikinCommandOffset.Mode.value)


def _daikin_ac_mode_to_hex() -> Dict[DaikinAcMode, List[HexValue]]:
    ac_mode_partial = partial(HexValue, offset=DaikinCommandOffset.Mode.value)
    off_marker_disabled = HexValue(0x00, DaikinCommandOffset.OffMarker.value)
    off_marker_enabled = HexValue(0x80, DaikinCommandOffset.OffMarker.value)

    values = {
        DaikinAcMode.Heat: [ac_mode_partial(0x49), _button_partial(DaikinAcButtons.ModeHeat.value), off_marker_disabled],
        DaikinAcMode.Cool: [ac_mode_partial(0x39), _button_partial(DaikinAcButtons.ModeCool.value), off_marker_disabled],
        DaikinAcMode.Dry: [ac_mode_partial(0x29), _button_partial(DaikinAcButtons.ModeDry.value), off_marker_disabled],
        DaikinAcMode.Fan: [ac_mode_partial(0x69), _button_partial(DaikinAcButtons.ModeFan.value), off_marker_disabled],
        DaikinAcMode.Auto: [ac_mode_partial(0x09), _button_partial(DaikinAcButtons.ModeAuto.value), off_marker_disabled],
        DaikinAcMode.Off: [_button_partial(DaikinAcButtons.Off), off_marker_enabled],
    }

    return values


def _daikin_fan_mode_to_hex() -> Dict[DaikinFanMode, List[HexValue]]:
    values = {
        DaikinFanMode.Auto: [_fan_swing_mode_partial(0xA0)],
        DaikinFanMode.Quiet: [_fan_swing_mode_partial(0xB0)],
        DaikinFanMode.Low: [_fan_swing_mode_partial(0x30)],
        DaikinFanMode.LowMid: [_fan_swing_mode_partial(0x40)],
        DaikinFanMode.Mid: [_fan_swing_mode_partial(0x50)],
        DaikinFanMode.MidHigh: [_fan_swing_mode_partial(0x60)],
        DaikinFanMode.High: [_fan_swing_mode_partial(0x70)],
    }

    return values


def _daikin_swing_mode_to_hex() -> Dict[DaikinSwingMode, List[HexValue]]:
    swing_mode_partial = partial(HexValue, offset=DaikinCommandOffset.SwingMode.value)
    fan_swing_non_auto = _fan_swing_mode_partial(0x00)
    values = {
        DaikinSwingMode.Auto: [swing_mode_partial(0x00), _fan_swing_mode_partial(0x0F)],
        DaikinSwingMode.Low: [swing_mode_partial(0x50), fan_swing_non_auto],
        DaikinSwingMode.LowMid: [swing_mode_partial(0x40), fan_swing_non_auto],
        DaikinSwingMode.Mid: [swing_mode_partial(0x30), fan_swing_non_auto],
        DaikinSwingMode.MidHigh: [swing_mode_partial(0x20), fan_swing_non_auto],
        DaikinSwingMode.High: [swing_mode_partial(0x10), fan_swing_non_auto],
    }

    return values


################################################## Private converters ##################################################
def _get_ac_mode_commands(
    mode: DaikinAcMode, on_timer: Optional[int] = None, off_timer: Optional[int] = None, previous_mode: Optional[DaikinAcMode] = None
) -> List[HexValue]:
    on_timer_mask = 0x0B
    off_timer_mask = 0x0D
    on_off_timer_mask = 0x0F

    if mode is DaikinAcMode.Off:
        if previous_mode is not None and previous_mode is not DaikinAcMode.Off:
            # previous_hex = _daikin_ac_mode_to_hex()[previous_mode]
            # return previous_hex - 1
            raise Exception("Not ready yet")
        else:
            commands = _daikin_ac_mode_to_hex()[mode]
            commands.append(_default_off_command)
            return commands
    else:
        commands  = _daikin_ac_mode_to_hex()[mode]

        predicate = lambda x: 0 < x <= 12
        on_timer_enabled = is_not_none_and(on_timer, predicate)
        off_timer_enabled = is_not_none_and(off_timer, predicate)
        if on_timer_enabled or off_timer_enabled:

            if on_timer_enabled and off_timer_enabled:
                mask = on_off_timer_mask
            elif on_timer_enabled:
                mask = on_timer_mask
            elif off_timer_enabled:
                mask = off_timer_mask

            new_mode = commands[0].value ^ mask
            commands[0].value = new_mode

    return commands

def _get_timers_commands(on_duration: int, off_duration: int) -> List[HexValue]:
    on_multiplier = 60  # Minutes
    off_multiplier = 960  # 60 Minutes * 16 ???

    values = [0x00, 0x06, 0x60]  # Default values for "both timers are 0"
    if 0 < on_duration <= 12:
        on_encoded = struct.pack("<H", on_duration * on_multiplier)
        values[0] = on_encoded[0]
        values[1] = on_encoded[1]
    if 0 < off_duration <= 12:
        off_encoded = struct.pack("<H", off_duration * off_multiplier)
        values[2] = off_encoded[1]
        values[1] = values[1] ^ off_encoded[0]

    offsets = [DaikinCommandOffset.Timer1, DaikinCommandOffset.Timer2, DaikinCommandOffset.Timer3]
    commands = []
    for (value, offset) in zip(values, offsets):
        commands.append(HexValue(value, offset.value))

    return commands


def _get_temperature_commands(mode: DaikinAcMode, temperature: int) -> List[HexValue]:
    temperature_partial = partial(HexValue, offset=DaikinCommandOffset.Temperature.value)
    temperature_mode_zero = HexValue(0x00, DaikinCommandOffset.TemperatureMode.value)
    temperature_mode_dry_auto = HexValue(0x80, DaikinCommandOffset.TemperatureMode.value)

    commands = []
    if mode in [DaikinAcMode.Heat, DaikinAcMode.Cool]:
        if 18 <= temperature <= 30:
            commands.append(temperature_partial(temperature * 2))
            commands.append(temperature_mode_zero)
        else:
            raise Exception(f"Temperature {temperature} out of bounds for mode {mode.name}! Allowed values are +18..+30C")
    elif mode is DaikinAcMode.Fan:
        commands.append(temperature_partial(0x32))  # Static value of 50 (25C)
        commands.append(temperature_mode_zero)
    elif mode is DaikinAcMode.Dry:
        commands.append(temperature_partial(0xC0))  # Static value
        commands.append(temperature_mode_dry_auto)
    elif mode is DaikinAcMode.Auto:
        if -5 <= temperature <= +5:
            offset = 0xC0 if temperature >= 0 else 0xE0
            value = offset + (temperature * 2)

            commands.append(HexValue(value, DaikinAcMode))
            commands.append(temperature_mode_dry_auto)
        else:
            raise Exception(f"Temperature {temperature} out of bounds for Auto mode! Allowed values are -5..+5C")
    return commands


def _get_fan_swing_commands(fan_mode: DaikinFanMode, swing_mode: DaikinSwingMode, no_wind: bool = False) -> List[HexValue]:
    no_wind_off: HexValue = HexValue(0x00, DaikinCommandOffset.NoWind.value)
    no_wind_on: HexValue = HexValue(0x01, DaikinCommandOffset.NoWind.value)

    if no_wind is False:
        fan_commands = _daikin_fan_mode_to_hex()[fan_mode]
        swing_commands = _daikin_swing_mode_to_hex()[swing_mode]

        fan_swing_mode_predicate = lambda x: x.offset == DaikinCommandOffset.FanSwingMode
        fan_mode_hex_part = find_first(fan_commands, fan_swing_mode_predicate)
        swing_mode_hex_part = find_first(swing_commands, fan_swing_mode_predicate)

        fan_swing_mode_hex = fan_mode_hex_part.value ^ swing_mode_hex_part.value

        combined_commands = []
        combined_commands.extend(fan_commands)
        combined_commands.extend(swing_commands)
        combined_commands = [value for value in combined_commands if value.offset is not DaikinCommandOffset.FanSwingMode.value]
        combined_commands.append(_fan_swing_mode_partial(fan_swing_mode_hex))
        combined_commands.append(no_wind_off)

        return combined_commands
    else:
        # no_wind mode disables both swing and fan control
        commands = []
        commands.append(HexValue(0x00, DaikinCommandOffset.SwingMode.value))
        commands.append(_fan_swing_mode_partial(0xA0))
        commands.append(no_wind_on)

        return commands


def _get_night_mode(night_mode: bool) -> List[HexValue]:
    value = 0x04 if night_mode else 0x00
    return [HexValue(value, DaikinCommandOffset.NightMode.value)]


def _get_frame_checksum(input: List[int]) -> int:
    sum = reduce(lambda x, y: x + y, input)
    checksum = sum & 0xFF

    return checksum


def _state_to_command(state: DaikinAcStateHolder, previous_state: Optional[DaikinAcStateHolder] = None) -> list[int]:
    result: List[int] = []
    result.extend(_frame_1_template)
    result.extend(_frame_2_template)

    state_commands: List[HexValue] = []
    state_commands.extend(_get_ac_mode_commands(state.mode, if_not_none(previous_state, lambda x: x.mode)))
    state_commands.extend(_get_temperature_commands(state.mode, state.temperature))
    state_commands.extend(_get_fan_swing_commands(state.fan_mode, state.swing_mode, state.no_wind))
    state_commands.extend(_get_timers_commands(state.on_timer_hours or 0, state.off_timer_hours or 0))
    state_commands.extend(_get_night_mode(state.night_mode))

    for command in state_commands:
        result[command.offset] = command.value

    frame_1_checksum = _get_frame_checksum(result[: DaikinCommandOffset.Frame1Checksum.value])
    frame_2_checksum = _get_frame_checksum(result[DaikinCommandOffset.Frame1Checksum.value + 1 : DaikinCommandOffset.Frame2Checksum.value])

    result[DaikinCommandOffset.Frame1Checksum.value] = frame_1_checksum
    result[DaikinCommandOffset.Frame2Checksum.value] = frame_2_checksum

    return result


################################################## Public state ##################################################
class DaikinAcState:
    def __init__(
        self,
        mode: DaikinAcMode,
        temperature: int,
        fan_mode: DaikinFanMode,
        swing_mode: DaikinSwingMode,
        no_wind: bool = False,
        night_mode: bool = False,
    ) -> None:
        state = DaikinAcStateHolder(
            mode=mode, temperature=temperature, fan_mode=fan_mode, swing_mode=swing_mode, no_wind=no_wind, night_mode=night_mode
        )
        self._state = state
        self._current_command = _state_to_command(self._state)

    def get_command(self):
        return self._current_command
