# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from dataclasses import dataclass
from typing import Generic, TypeVar

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

def tryCall(object, name: str, *args, **kwargs):
	if (object is not None):
		method = getattr(object, name)
		if(callable(method)): return method(*args, **kwargs)