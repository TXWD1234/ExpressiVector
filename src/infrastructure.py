# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .geometry import *
from dataclasses import dataclass, field
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

# ################ Text Processing ################

# ################ Font ################

@dataclass(slots=True)
class FontManager:
	data: dict[int, pygame.Font] = field(default_factory=dict[int, pygame.Font])

	def addFont(self, fontSize: int):
		self.data[fontSize] = pygame.font.SysFont(None, fontSize)

	# supports lazy loading
	def font(self, fontSize: int) -> pygame.Font:
		if (fontSize not in self.data): self.addFont(fontSize)
		return self.data[fontSize]

	# ================ Logic Helpers ================

	def findWidth(self, string: str, fontSize: int) -> int:
		return self.font(fontSize).size(string)[0]

	def findHeight(self, fontSize: int) -> int:
		return self.font(fontSize).get_linesize()

	def split(self, string: str, fontSize: int, width: int) -> list[str]:
		'''
		UB if a word is bigger then width
		UB if consecutive white spaces are present
		'''
		
		# this is the dumbest algorithm ever, but since it's written in python,
		# it is completely valid to be dumb, since that's what the language
		# sets out to do

		res = []

		lastSlice = 0 # next index after the ' '
		lastWord = 0 # index at ' '
		for i in range(len(string)):
			if (string[i] != ' '): continue
			if (self.findWidth(string[lastSlice:i], fontSize).x > width):
				# wrap
				res.append(string[lastSlice:lastWord])
				lastSlice = lastWord + 1
			lastWord = i

		res.append(string[lastSlice:])

		return res

	def findFontSizeViaHeight(self, lineHeight: int) -> int:
		return int(round((16384 / pygame.font.SysFont(None, 16384).get_linesize()) * lineHeight))

	# ================ Utility ================

	def renderSingle_impl(self, string: str, fontSize: int, color: Color) -> pygame.Surface:
		return self.font(fontSize).render(string, True, color)

	# auto center
	def renderLine(self, string: str, fontSize: int, color: Color) -> pygame.Surface:
		texture = self.font(fontSize).render(string, True, color)
		res = pygame.Surface((texture.get_width(), self.findHeight(fontSize)), flags=pygame.SRCALPHA)
		res.blit(texture, (0, (res.get_height() - self.font(fontSize).get_height()) // 2))
		return res
	
	def render(self, string: str, fontSize: int, color: Color, width: int = 0) -> tuple[pygame.Surface, int]:
		# worst code ive ever written, wastes a lot of cycles and memory, as well as semantically awful, but i don't care, this is python, i can do whatever i want 
		if (width == 0): return (self.renderLine(string, fontSize, color), 1)
		source = self.split(string, fontSize, width)
		if (len(source) == 1): return (self.renderLine(string, fontSize, color), 1)
		res = pygame.Surface((width, len(source) * self.findHeight(fontSize)), flags=pygame.SRCALPHA)
		pos = 0
		for s in source:
			res.blit(self.renderSingle_impl(s, fontSize, color), (0, pos))
			pos += self.findHeight(fontSize)
		return (res, len(source))