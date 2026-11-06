# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from dataclasses import dataclass
from typing import Generic, TypeVar
import inspect

T = TypeVar('T')

@dataclass(slots=True)
class Ptr(Generic[T]):
	v: T | None = None

	# Getter: a()
	# Setter: a(20)
	def __call__(self, *args: T) -> T:
		if args:
			self.v = args[0]
		return self.v


def is_invocable(func, *args, **kwargs) -> bool:
    try:
        # bind() simulates a call to check if the arguments map correctly
        inspect.signature(func).bind(*args, **kwargs)
        return True
    except TypeError:
        return False
	
def tryCall(object, name: str, *args, **kwargs):
	if (object is not None and hasattr(object, name) and
	    is_invocable((method := getattr(object, name)), *args, **kwargs)):
		return method(*args, **kwargs)

def optionalCall(func, arg):
	if (is_invocable(func, arg)):
		func(arg)
	else: func()

type Color = tuple[int, int, int]

def clamp[T](val: T, min_val: T, max_val: T) -> T:
    if val < min_val: return min_val
    if val > max_val: return max_val
    return val