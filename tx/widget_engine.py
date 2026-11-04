# Inspired by: Qt

from .geometry import *
from .rgb import *
from typing import Callable, Generic, TypeVar, Self
from pygame import draw
from dataclasses import dataclass, field	
from collections import deque

T = TypeVar('T')

@dataclass(slots=True)
class WidgetBase:
	'''
	Since the damn Python don't have templates and is weakly and dynamically
	typed, I am going to release the forbidden pattern: any type everything and
	constraint the types with convention.
	
	Convention is now defining how a type is a type. Basically type traits, or
	concepts. But instead of compiler forcing it, it all lives in the developer's
	head. And when he forget one, the entire thing dies.
	
	Widget Convention:
	requires (Widget w) {
		w.update() # update logic and input
		w.render() # attempt redraw (no draw if no chnage)
		w.draw() # force redraw
	}
	'''

	# ================ Object Lifetime ================

	widgets: list[Self] = field(default_factory=list)

	# ================ Main Loop Interface ================

	def update(self):
		for w in self.widgets:
			w.update()

	def render(self, screen: pygame.Surface):
		if(self.diff): self.draw(screen)
		else:
			for w in self.widgets:
				w.render(screen)

	def draw(self, screen: pygame.Surface):
		for w in self.widgets:
			w.draw(screen)

	# ================ Public Interface ================
	'''
	Strict Public Interface methods by definition must be called only by user manually, exclusively.
	'''

	def addWidget[T: WidgetBase](self, widget: T) -> T:
		self.widgets.append(widget)
		return widget

	def widget(self, index: int):
		return self.widgets[index]

	# ================ State ================

	diff: bool = True

@dataclass(slots=True)
class RectWidgetBase(WidgetBase):
	# ================ Main Loop Interface ================

	def draw(self, screen: pygame.Surface):
		draw.rect(screen, self.style.backgroundColor,
		          makeRect(self.pos, self.dim), 0,
		          border_radius = self.style.roundCornerRadius)
		super().draw(screen)
		self.diff = False

	# ================ Public Interface ================

	def addWidget[T: RectWidgetBase](self, widget: T) -> T:
		widget.pos += self.pos
		super().addWidget(widget)
		return widget

	# ================ Geometry ================

	'''
	After initialization, the geometry of the widget should not be modified by
	the object itself, or mnaually. It should only be modified by the parent's
	layout manager.
	'''

	pos: ivec2 = field(default_factory=lambda: ivec2(0, 0)) # position (topLeft)
	dim: ivec2 = field(default_factory=lambda: ivec2(0, 0)) # dimension

	# ================ Styling ================

	@dataclass(slots=True)
	class StyleSheet:
		backgroundColor: tuple[int, int, int] = Black
		roundCornerRadius: int = 0

	style: StyleSheet = field(default_factory=StyleSheet)

	def setStyleSheet(self, cb: Callable[[StyleSheet], StyleSheet]):
		cb(self.style)
		self.diff = True

@dataclass(slots=True)
class LinearLayoutAttribute:
	order: int = -1 # the index of the widget in the layout
	proportion: float = 1 # weight out of the total weight of all widgets;
	                      # absolute: minimum absolute proportion of the entire layout
	absolute: bool = False

@dataclass(slots=True)
class LinearLayoutSolver:

	# ================ Public Interface ================

	def addAttrib(self, attrib: LinearLayoutAttribute):
		self.widgetAttribs.append(attrib)

	def solve(self, basePos, baseLength: int, modifier: Callable[[int, int, int], None]):
		'''
		UB if sum of absoluteProportion is bigger then 1.
		UB if size of self.widgetAttribs mismatches size of parent widget array

		parameter `modifier` will be called with arguments (index, pos, length) aka (index, x, width) / (index, y, height)
		'''
		masterProportion: int = sum(i.proportion * (not i.absolute) for i in self.widgetAttribs) # the total weight of all widgets
		absoluteConsumption: int = sum(i.proportion * (i.absolute) for i in self.widgetAttribs) * baseLength
		unit: float = (baseLength - absoluteConsumption) / masterProportion if masterProportion > 0 else 0
		
		acc: float = basePos
		orderIndexArray = sorted(range(len(self.widgetAttribs)), key = lambda i: self.widgetAttribs[i].order)
		for i in orderIndexArray:
			length = self.widgetAttribs[i].proportion * (baseLength if self.widgetAttribs[i].absolute else unit)
			modifier(i, int(round(acc)), int(math.floor(length)))
			acc += length

	# ================ State ================
	
	widgetAttribs: list[LinearLayoutAttribute] = field(default_factory=list)

# Horizontal Layout
@dataclass(slots = True)
class RectWidgetHLayout(RectWidgetBase):
	solver: LinearLayoutSolver = field(default_factory=LinearLayoutSolver)

	def modifier_impl(self, i: int, x: int, w: int):
		self.widgets[i].pos.x = x
		self.widgets[i].dim.x = w
	
	def addWidget[T: RectWidgetBase](self, widget: T, layoutAttrib: LinearLayoutAttribute) -> T:
		super().addWidget(widget)
		widget.dim.y = self.dim.y
		self.solver.addAttrib(layoutAttrib)
		self.diff = True
		return widget

	def activateLayout(self):
		self.solver.solve(self.pos.x, self.dim.x, self.modifier_impl)

# Vertical Layout
@dataclass(slots = True)
class RectWidgetVLayout(RectWidgetBase):
	solver: LinearLayoutSolver = field(default_factory=LinearLayoutSolver)

	def modifier_impl(self, i: int, y: int, h: int):
		self.widgets[i].pos.y = y
		self.widgets[i].dim.y = h
	
	def addWidget[T: RectWidgetBase](self, widget: T, layoutAttrib: LinearLayoutAttribute) -> T:
		super().addWidget(widget)
		widget.dim.x = self.dim.x
		self.solver.addAttrib(layoutAttrib)
		self.diff = True
		return widget

	def activateLayout(self):
		self.solver.solve(self.pos.y, self.dim.y, self.modifier_impl)


class WidgetEngine [T: WidgetBase]:
	def __init__(self, windowDimension: ivec2, BaseWidgetType: type[T]):
		self.screen = self.screen = pygame.display.set_mode((windowDimension.x, windowDimension.y))
		self.baseWidget = BaseWidgetType(dim = windowDimension)

	def base(self) -> T:
		return self.baseWidget

	def render(self):
		self.baseWidget.render(self.screen)

	def update(self):
		self.baseWidget.update()