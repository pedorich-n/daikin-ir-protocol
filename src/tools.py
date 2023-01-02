from typing import List, Callable, TypeVar, Optional

A = TypeVar("A")
B = TypeVar("B")


def find_first(list: List[A], predicate: Callable[[A], bool]) -> Optional[A]:
    return next(filter(predicate, list), None)


def print_list(list: List[A]) -> str:
    return str([str(value) for value in list])


def if_not_none(value: Optional[A], f: Callable[[A], B]) -> Optional[B]:
    return f(value) if value is not None else None
