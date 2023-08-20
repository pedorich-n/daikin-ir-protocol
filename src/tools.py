from typing import List, Callable, TypeVar, Optional

A = TypeVar("A")
B = TypeVar("B")


def find_first(list: List[A], predicate: Callable[[A], bool]) -> Optional[A]:
    return next(filter(predicate, list), None)


def if_not_none(value: Optional[A], f: Callable[[A], B]) -> Optional[B]:
    return f(value) if value is not None else None


def is_not_none_and(value: Optional[A], predicate: Callable[[A], bool]) -> bool:
    return value is not None and predicate(value)

