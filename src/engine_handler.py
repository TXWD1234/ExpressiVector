# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .infrastructure import *
from .engine import *

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Generic, TypeVar, Self, Any, ClassVar, TYPE_CHECKING
import pygame

class EngineState(Enum):
	Normal = auto()
	Drag = auto()
	Edit = auto() # during the performance of an edit action

class EditStateTag(Enum):
	Nothing = auto() # selecting no tool
	Stroke = auto()
	ColorPick = auto()

# ################ Globals ################

class WidgetState(Enum):
	Normal = auto()
	Focused = auto()

if TYPE_CHECKING:
    from .widgets import ApplicationWidget

@dataclass(slots=True)
class Global:
	widgetState: WidgetState = WidgetState.Normal
	focusWidget: Any | None = None
	font: FontManager = field(default_factory=FontManager)
	engine: Engine = field(default_factory=Engine)
	engineState: list[EngineState] = field(default_factory=lambda: [EngineState.Normal])
	editStateTag: list[EditStateTag] = field(default_factory=lambda: [EditStateTag.Nothing])
	editState: dict = field(default_factory=lambda: {
		EditStateTag.Stroke: Engine.StrokeConfig()})
	app: ApplicationWidget | None = None # ApplicationWidget
	redraw: bool = False # redraw the entire UI
	unit: int = 32 # unit dictating the size of all widgets
	fontSize: int = 0

@dataclass(slots=True)
class EngineHandler:
	'''
	Handles Edit State, dispatcher of engine APIs.
	'''

	uniform: Global | None = None

	# ================ Public Interface ================
	'''
	Guaranteed by upsteam that event is left mouse, and editStateTag is not
	Nothing.
	'''

	def handleMouseDown(self, vpPos: vec2):
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Stroke:
				self.uniform.engine.strokeCreate(
					vpPos,
					self.uniform.editState[EditStateTag.Stroke])

	def handleMouseMotion(self, vpPos: vec2):
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Stroke:
				self.uniform.engine.strokeAppend(vpPos)