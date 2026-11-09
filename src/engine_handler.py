# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from enum import Enum, auto

class EngineState(Enum):
	Normal = auto()
	Drag = auto()
	Edit = auto() # during the performance of an edit action

class EditState(Enum):
	Nothing = auto() # selecting no tool
	Stroke = auto()