from typing import List, Tuple, Union

Space_Zero = 435
Space_One = 1300
Mark = 435

_prefix = [Mark, -Space_Zero, Mark, -Space_Zero, Mark, -Space_Zero, Mark, -Space_Zero, Mark, -Space_Zero, Mark, -24900]
_header = [3500, -1750]
_pause_between_frames = -34900


def encode_bit(bit: Union[bool, str, int]) -> Tuple[int, int]:
    if bit is True or bit == "1" or bit == 1:
        return (Mark, -Space_One)
    elif bit is False or bit == "0" or bit == 0:
        return (Mark, -Space_Zero)


def encode_list(list: List[int]) -> List[int]:
    result = []
    for num in list:
        bits = format(num, "08b")
        for bit in bits:
            result.extend(encode_bit(bit))

    return result


def encode_command(command: List[int]) -> List[int]:
    frame_1 = command[:20]
    frame_2 = command[20:]

    pulses = []

    pulses.extend(_prefix)

    pulses.extend(_header)
    pulses.extend(encode_list(frame_1))
    pulses.append(Mark)

    pulses.append(_pause_between_frames)

    pulses.extend(_header)
    pulses.extend(encode_list(frame_2))
    pulses.append(Mark)

    return pulses
