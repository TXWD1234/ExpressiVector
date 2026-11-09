# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .geometry import *
from dataclasses import dataclass
from typing import Generic, TypeVar
from pathlib import Path
import pygame
import inspect
import sys

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

def scaleToFit(src: ivec2, target: ivec2) -> ivec2:
	wr = target.x / src.x
	hr = target.y / src.y
	# if (wr > hr) then it's height bound
	r = min(wr, hr)
	return ivec2(src.x * r, src.y * r)

def scaleToFit(src: ivec2, target: ivec2) -> ivec2:
	r = min(target.x / src.x, target.y / src.y)
	return ivec2(src.x * r, src.y * r)

def getProgramDir() -> Path:
	if hasattr(sys, '_MEIPASS'): # when running in pyinstaller executable
		return Path(sys._MEIPASS)
	return Path(__file__).parent.parent