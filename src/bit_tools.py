import struct
from typing import List


# Shamelessly taken from https://stackoverflow.com/a/12682003
def reverse_bits(number: int, width: int = 8) -> int:
    bits = "{:0{width}b}".format(number, width=width)
    return int(bits[::-1], 2)


def lsb_command_to_msb(command: List[int]) -> List[int]:
    return [reverse_bits(num) for num in command]

def stringify_command(command: List[int], spaces: bool = False) -> str:
    packed = struct.pack(f">{len(command)}B", *command)
    separator = " " if spaces else ""
    string = bytearray(packed).hex(sep=separator).upper()

    return string