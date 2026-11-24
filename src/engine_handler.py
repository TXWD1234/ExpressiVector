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
	Rect = auto()
	ColorPick = auto()
	FileExplore = auto()
	FileOp = auto()
	Stamp = auto()
	Line = auto()
	Oval = auto()

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
		EditStateTag.Stroke: Engine.StrokeConfig(),
		EditStateTag.Rect: Engine.RectConfig(),
		EditStateTag.Stamp: Engine.StampConfig(),
		EditStateTag.Line: Engine.StrokeConfig(),
		EditStateTag.Oval: Engine.OvalConfig()
		})
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

	def endSession_impl(self):
		while (len(self.uniform.engineState) > 1): self.uniform.engineState.pop()

	# ================ Public Interface ================
	'''
	Guaranteed by upsteam that event is left mouse, and editStateTag is not
	Nothing.
	'''

	inProgress: bool = False

	def cancel(self, prevState: EditStateTag):
		match (prevState):
			case EditStateTag.Rect:
				if (self.inProgress): self.uniform.engine.rectCancel()
			case EditStateTag.Oval:
				if (self.inProgress): self.uniform.engine.ovalCancel()
			case EditStateTag.Line:
				if (self.inProgress): self.uniform.engine.lineCancel()
		self.inProgress = False
		self.endSession_impl()

	def handleMouseDown(self, vpPos: vec2):
		self.uniform.engine.previewPoint = vpPos
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Stroke:
				self.uniform.engine.strokeCreate(
					vpPos, self.uniform.editState[EditStateTag.Stroke])
			case EditStateTag.Rect:
				if (not self.inProgress):
					self.uniform.engine.rectCreate(
						vpPos, self.uniform.editState[EditStateTag.Rect])
					self.inProgress = True
				else:
					self.uniform.engine.rectFinish(vpPos)
					self.inProgress = False
					self.endSession_impl()
			case EditStateTag.Oval:
				if (not self.inProgress):
					self.inProgress = True
					self.uniform.engine.ovalCreate(
						vpPos, self.uniform.editState[EditStateTag.Oval])
				else:
					self.inProgress = False
					self.uniform.engine.ovalFinish(vpPos)
					self.endSession_impl()
			case EditStateTag.Stamp:
				if (self.uniform.editState[EditStateTag.Stamp].textureId == -1): return
				self.uniform.engine.stampCreate(
					vpPos, self.uniform.editState[EditStateTag.Stamp])
			case EditStateTag.Line:
				if (not self.inProgress):
					self.inProgress = True
					self.uniform.engine.lineCreate(
						vpPos, self.uniform.editState[EditStateTag.Line])
				else:
					self.uniform.engine.lineAppend(vpPos)

	# @return diff
	def handleMouseDownRight(self, vpPos: vec2) -> bool:
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Line: self.cancel(EditStateTag.Line)
			case EditStateTag.Oval: self.cancel(EditStateTag.Oval)
			case EditStateTag.Rect: self.cancel(EditStateTag.Rect)
			case _:
				return False
		return True

	def handleMouseUp(self, vpPos: vec2):
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Stroke: self.endSession_impl()
			case EditStateTag.Stamp: self.endSession_impl()

	def handleMouseMotion(self, vpPos: vec2):
		self.uniform.engine.previewPoint = vpPos
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Stroke: self.uniform.engine.strokeAppend(vpPos)
			case EditStateTag.Stamp:
				if (self.uniform.editState[EditStateTag.Stamp].textureId == -1): return
				self.uniform.engine.stampCreate(
					vpPos, self.uniform.editState[EditStateTag.Stamp])

	# @return diff
	# this is basically normal state preview register
	def handleMouseMotionNormal(self, vpPos: vec2) -> bool:
		self.uniform.engine.previewPoint = vpPos
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Stroke: return True
			case EditStateTag.Stamp: return True
			case EditStateTag.Line: return True
		return False