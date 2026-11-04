# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.
# Inspired by: Qt

from .geometry import *
from .rgb import *
from typing import Callable, Generic, TypeVar, Self
from pygame import draw
from dataclasses import dataclass, field, replace
from collections import deque

T = TypeVar('T')

# ################ Widget Basics ################
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

	w.handleEvent() # handle an event; return whether the event is handled
	# Must call RectWidgetBase.handleEvent()
}
'''

@dataclass(slots=True)
class WidgetBase:
	'''
	Base Widget class of all widgets. Only manages sub widget tree. Does not
	consist geometry therefore is fundamentally not part of the normal widget
	system. It should never be used individually.
	'''
	
	# ================ Object Lifetime ================

	widgets: list[Self] = field(default_factory=list)
	
	parent: WidgetBase | None = None
	id: int = 0

	# ================ Contract Interface ================

	def update(self):
		for w in self.widgets:
			w.update()

	def render(self, screen: pygame.Surface):
		if (self.diff):
			self.draw(screen)
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
		widget.parent = self
		widget.id = len(self.widgets)
		self.widgets.append(widget)
		return widget

	def widget(self, index: int):
		return self.widgets[index]

	# ================ State ================

	diff: bool = True

@dataclass(slots=True)
class RectWidgetBase(WidgetBase):
	# ================ Contract Interface ================

	def draw(self, screen: pygame.Surface):
		draw.rect(screen, self.style.backgroundColor,
		          makeRect(self.pos + ivec2(self.style.margin, self.style.margin),
		                   self.dim - ivec2(self.style.margin * 2, self.style.margin * 2)), 0,
		          border_radius = self.style.roundCornerRadius)
		super().draw(screen)
		self.diff = False


	# ================ Public Interface ================

	def addWidget[T: RectWidgetBase](self, widget: T) -> T:
		widget.pos += self.pos
		super().addWidget(widget)
		return widget

	def hide(self):
		self.dim = ivec2(0, 0)
		if (hasattr(self.parent, 'solver') and isinstance(self.parent.solver, LinearLayoutSolver)):
			self.parent.solver.widgetAttribs[self.id].visible = False
			self.parent.activateLayout()
	def show(self):
		if (hasattr(self.parent, 'solver') and isinstance(self.parent.solver, LinearLayoutSolver)):
			self.parent.solver.widgetAttribs[self.id].visible = True
			self.parent.activateLayout()

	def visible(self) -> bool:
		if (hasattr(self.parent, 'solver') and isinstance(self.parent.solver, LinearLayoutSolver)):
			return self.parent.solver.widgetAttribs[self.id].visible
		return True
		
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
		margin: int = 0

	style: StyleSheet = field(default_factory=StyleSheet)

	def setStyleSheet(self, cb: Callable[[StyleSheet], StyleSheet]):
		self.style = cb(self.style)
		self.diff = True

	# ================ Event Handling ================
	'''
	Events are processed in the following policies:
	- Mouse Events: Dispatched according to the position of the mouse, invoked
	                at the front most widget and propagate up
	- Keyboard Events: Dispatched to the currently focusing widget, and
	                   further to the global keybind manager
	- Window Events: Handled directly here
	'''

	def subWidgetHandleEvent_impl(self, event: pygame.Event, pos: ivec2) -> bool:
		if (len(self.widgets) == 0): return False
		for w in self.widgets:
			if (issubclass(type(w), RectWidgetBase) and
			    inRange(makeRect(w.pos, w.dim), pos)):
				return w.handleEvent(event)
		return False

	def handleEvent(self, event: pygame.Event) -> bool:
		match event.type:
			case pygame.MOUSEBUTTONDOWN | pygame.MOUSEBUTTONUP:
				return self.subWidgetHandleEvent_impl(
					event, ivec2(event.pos[0], event.pos[1]))
			case pygame.MOUSEMOTION:
				
				return False
			case pygame.KEYDOWN | pygame.KEYUP:
				return False
			case pygame.TEXTINPUT:
				return False
			case _:
				return False

@dataclass(slots=True)
class LinearLayoutAttribute:
	order: int = -1 # the index of the widget in the layout
	proportion: float = 1 # weight out of the total weight of all widgets;
	                      # absolute: minimum absolute proportion of the entire layout
	absolute: bool = False
	visible: bool = True

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
		masterProportion: int = sum(i.proportion for i in self.widgetAttribs if i.visible and (not i.absolute)) # the total weight of all widgets
		absoluteConsumption: int = sum(i.proportion for i in self.widgetAttribs if i.visible and i.absolute) * baseLength
		unit: float = (baseLength - absoluteConsumption) / masterProportion if masterProportion > 0 else 0
		
		acc: float = basePos
		orderIndexArray = sorted(range(len(self.widgetAttribs)), key = lambda i: self.widgetAttribs[i].order)
		for i in orderIndexArray:
			if (not self.widgetAttribs[i].visible): continue
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
		self.solver.addAttrib(layoutAttrib)
		return widget

	def activateLayout(self):
		'''recursive'''
		for w in self.widgets: w.dim.y = self.dim.y
		self.solver.solve(self.pos.x, self.dim.x, self.modifier_impl)
		for w in self.widgets:
			if (hasattr(w, 'activateLayout') and callable(w.activateLayout)):
				w.activateLayout()
		self.diff = True

# Vertical Layout
@dataclass(slots = True)
class RectWidgetVLayout(RectWidgetBase):
	solver: LinearLayoutSolver = field(default_factory=LinearLayoutSolver)

	def modifier_impl(self, i: int, y: int, h: int):
		self.widgets[i].pos.y = y
		self.widgets[i].dim.y = h
	
	def addWidget[T: RectWidgetBase](self, widget: T, layoutAttrib: LinearLayoutAttribute) -> T:
		super().addWidget(widget)
		self.solver.addAttrib(layoutAttrib)
		return widget

	def activateLayout(self):
		for w in self.widgets: w.dim.x = self.dim.x
		self.solver.solve(self.pos.y, self.dim.y, self.modifier_impl)
		for w in self.widgets:
			if (hasattr(w, 'activateLayout') and callable(w.activateLayout)):
				w.activateLayout()
		self.diff = True




# ################ Input Handler ################

class InputHandler:

	# ================ Public Interface ================
	
	@staticmethod
	def handle(baseWidget: RectWidgetBase) -> bool:
		'''
		Return whether the program will continue running
		'''
		for event in pygame.event.get():
			if (event.type == pygame.QUIT): return False
			baseWidget.handleEvent(event)
			
		return True


# ################ Widgets ################

@dataclass(slots=True)
class PushButtonWidget(RectWidgetBase):
	'''
	This class also serves as a demo of the Event Handling system
	'''

	onPress: Callable[[PushButtonWidget], None] = field(default_factory=lambda _: None)

	# ================ Contract Interface ================
	
	def handleEvent(self, event):
		if (super().handleEvent(event)): return True # process sub widgets
		# sub widgets not handled - attempt handling for this widget
		if (event.type == pygame.MOUSEBUTTONDOWN):
			self.onPress(self)
			return True
		return False

	# ================ Public Interface ================
	
	







class WidgetEngine [T: RectWidgetBase]:
	'''
	Highest level wrapper of the widget system
	'''

	def __init__(self, windowDimension: ivec2, BaseWidgetType: type[T]):
		self.screen = self.screen = pygame.display.set_mode((windowDimension.x, windowDimension.y))
		self.baseWidget = BaseWidgetType(dim = windowDimension)

	def base(self) -> T:
		return self.baseWidget

	def render(self):
		self.baseWidget.render(self.screen)

	def update(self) -> bool:
		self.baseWidget.update()
		return InputHandler.handle(self.baseWidget)