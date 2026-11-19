# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.
# Inspired by: Qt

from __future__ import annotations
from .geometry import *
from .rgb import *
from .infrastructure import *
from .engine import *
from .engine_handler import *
from typing import Callable, Generic, TypeVar, Self, Any, ClassVar, TYPE_CHECKING
from pygame import draw
from dataclasses import dataclass, field, replace, InitVar
from collections import deque
from enum import Enum, auto

T = TypeVar('T')

class Events:
	MouseEnter: int = pygame.event.custom_type()
	MouseLeave: int = pygame.event.custom_type()

DefaultColor = Magenta

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

	w.activateLayout()
	w.reportHeight()
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

	uniform: Global | None = None

	# ================ Contract Interface ================

	def update(self):
		for w in self.widgets:
			w.update()

	def render(self, screen: pygame.Surface):
		if (self.diff or
		    (self.overlay is not None and self.overlay.diff) or
			self.uniform.redraw):
			self.draw(screen)
		else:
			for w in self.widgets:
				w.render(screen)

	def draw(self, screen: pygame.Surface):
		for w in self.widgets:
			if (w.visible()): w.draw(screen)
		self.diff = False

	# ================ Public Interface ================
	'''
	Strict Public Interface methods by definition must be called only by user manually, exclusively.
	'''

	def addWidget[T: WidgetBase](self, widgetType: type[T], **args) -> T:
		widget = widgetType(**(args | {
				"parent": self,
				"id": len(self.widgets),
				"uniform": self.uniform
			}))
		self.widgets.append(widget)
		return widget

	# deprecated
	def widget(self, index: int):
		return self.widgets[index]

	# ================ State ================

	diff: bool = True
	overlay: OverlayBase | None = None

@dataclass(slots=True)
class RectWidgetBase(WidgetBase):
	# ================ Contract Interface ================

	def render(self, screen):
		if (not self.visible()): return
		return super().render(screen)

	def draw(self, screen: pygame.Surface):
		rect = makeRect(self.pos + ivec2(self.styleSheet.margin, self.styleSheet.margin),
						self.dim - ivec2(self.styleSheet.margin * 2, self.styleSheet.margin * 2))
		draw.rect(screen,
		          self.state.colorOverride if self.state.colorOverride is not None else
				  (self.styleSheet.hoverColor if self.state.hover else self.styleSheet.backgroundColor),
		          rect, border_radius=self.styleSheet.roundCornerRadius)
		if (self.styleSheet.borderWidth != 0):
			draw.rect(screen, self.styleSheet.hoverBorderColor if self.state.hover else self.styleSheet.borderColor, rect,
			          width=self.styleSheet.borderWidth,
					  border_radius=self.styleSheet.roundCornerRadius)
		tryCall(self.overlay, "draw", screen, self)
		super().draw(screen)
		self.diff = False

	def activateLayout(self):
		#for w in self.widgets: tryCall(w, "activateLayout")
		for w in self.widgets: w.activateLayout()
		self.diff = True

	def reportHeight(self): return 1

	# ================ Public Interface ================

	def addWidget[T: RectWidgetBase](self, widgetType: type[T], **args) -> T:
		widget = super().addWidget(widgetType, **({
			"theme": self.theme,
			"styleSheet": replace(self.theme[widgetType]) if widgetType in self.theme else None
		} | args))
		return widget

	def hide(self):
		self.dim = ivec2(0, 0)
		if (hasattr(self.parent, 'solver') and (isinstance(self.parent.solver, LinearLayoutSolver) or isinstance(self.parent.solver, UnitedLinearLayoutSolver))):
			self.parent.solver.widgetAttribs[self.id].visible = False
			self.parent.activateLayout()
			self.parent.activateLayout()
	def show(self):
		if (hasattr(self.parent, 'solver') and (isinstance(self.parent.solver, LinearLayoutSolver) or isinstance(self.parent.solver, UnitedLinearLayoutSolver))):
			self.parent.solver.widgetAttribs[self.id].visible = True
			self.parent.activateLayout()
			self.parent.activateLayout()
			self.diff = True

	def visible(self) -> bool:
		if (hasattr(self.parent, 'solver') and (isinstance(self.parent.solver, LinearLayoutSolver) or isinstance(self.parent.solver, UnitedLinearLayoutSolver))):
			return self.parent.solver.widgetAttribs[self.id].visible
		return True

	def move(self, delta: ivec2):
		self.pos += delta
		for w in self.widgets: w.move(delta)
		
	# ================ Geometry ================

	'''
	After initialization, the geometry of the widget should not be modified by
	the object itself, or manually. It should only be modified by the parent's
	layout manager.
	'''

	pos: ivec2 = field(default_factory=lambda: ivec2(0, 0)) # position (topLeft)
	dim: ivec2 = field(default_factory=lambda: ivec2(0, 0)) # dimension

	# ================ State ================

	@dataclass(slots=True)
	class State:
		hover: bool = False
		colorOverride: Color | None = None
	state: State = field(default_factory=State)

	# ================ Styling ================
	'''
	Theme and StyleSheet should only be set in configure time, and remain constant in runtime.
	The appearance is governed by the style sheet, determinded by the state;
	The StyleSheet is default to the Theme. It can, however, be customised per widget instance.
	'''

	@dataclass(slots=True)
	class StyleSheet:
		backgroundColor: Color = DefaultColor
		hoverColor: Color = DefaultColor
		roundCornerRadius: int = 0
		margin: int = 0
		borderWidth: int = 0
		borderColor: Color = DefaultColor
		hoverBorderColor: Color = DefaultColor

	theme: WidgetTheme | None = None
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

	# deprecated
	def setStyleSheet(self, cb: Callable[[StyleSheet], StyleSheet]):
		self.styleSheet = cb(self.styleSheet)
		self.diff = True

	def setOverlay[T: OverlayBase](self, overlayType: type[T], **args) -> T:
		self.overlay = overlayType(**({
			"styleSheet": replace(self.theme[overlayType]),
			"uniform": self.uniform
		} | args))
		return self.overlay

	# ================ Event Handling ================
	'''
	Events are processed in the following policies:
	- Mouse Events: Dispatched according to the position of the mouse, invoked
	                at the front most widget and propagate up
	- Keyboard Events: Dispatched to the currently focusing widget, and
	                   further to the global keybind manager
	- Window Events: Handled directly here
	'''

	hoverWidget: RectWidgetBase | None = None

	def subWidgetFindWithin_impl(self, pos: ivec2) -> RectWidgetBase:
		for w in self.widgets:
			# if (issubclass(type(w), RectWidgetBase) and
			# 	inRange(makeRect(w.pos, w.dim), pos)): return w
			if (inRange(makeRect(w.pos + ivec2(w.styleSheet.margin), w.dim - ivec2(w.styleSheet.margin) * 2), pos)): return w
		return self

	def subWidgetHandleCollisionEvent_impl(self, event: pygame.Event, pos: ivec2) -> bool:
		if (len(self.widgets) == 0): return False
		if ((w := self.subWidgetFindWithin_impl(pos)) is not self): return w.handleEvent(event)
		return False

	def subWidgetHandleEvent_impl(self, event: pygame.Event) -> bool:
		for w in self.widgets: w.handleEvent(event)

	def handleEvent(self, event: pygame.Event) -> bool:
		match (event.type):
			case pygame.MOUSEBUTTONDOWN | pygame.MOUSEBUTTONUP:
				return self.subWidgetHandleCollisionEvent_impl(
					event, ivec2(event.pos[0], event.pos[1]))
			case pygame.MOUSEMOTION:
				# When received a mouse motion event, assume it's all-within
				if (not self.handleMouseDisplacement(ivec2.fromTuple(event.pos)) and self.hoverWidget is not self):
					self.hoverWidget.handleEvent(event)
				return False
			case Events.MouseEnter:
				if ((sub := self.subWidgetFindWithin_impl(event.pos)) is not self):
					sub.handleEvent(event)
					self.hoverWidget = sub
				self.state.hover = True
				self.diff = True
				return False
			case Events.MouseLeave:
				if (self.hoverWidget is not None and self.hoverWidget is not self):
					self.hoverWidget.handleEvent(event)
					self.hoverWidget = None
				self.state.hover = False
				self.diff = True
				return False
			case _:
				return self.subWidgetHandleEvent_impl(event)

	def handleMouseDisplacement(self, pos: ivec2) -> bool:
		curW = self.subWidgetFindWithin_impl(pos)
		fromW = self.hoverWidget
		if (fromW is curW): return False
		else:
			if (fromW is not self): tryCall(fromW, "handleEvent", pygame.Event(Events.MouseLeave))
			if (curW   is not self):             curW.handleEvent(pygame.Event(Events.MouseEnter, {"pos": pos}))
			self.hoverWidget = curW
			return True

	def subWidgetHandleMouseDisplacement(self, pos: ivec2):
		for w in self.widgets:
			if (not w.handleMouseDisplacement(pos)):
				w.subWidgetHandleMouseDisplacement(pos)

	# ================ Internal Utility ================

	def enterFocus(self):
		self.uniform.widgetState = WidgetState.Focused
		self.uniform.focusWidget = self

	def exitFocus(self):
		self.uniform.widgetState = WidgetState.Normal
		self.uniform.focusWidget = None
		self.refreshHover(ivec2.fromTuple(pygame.mouse.get_pos()))

	def refreshHover(self, pos: ivec2):
		self.state.hover = inRange(makeRect(self.pos, self.dim), pos)
		self.diff = True
		
@dataclass(slots=True)
class TransparentRectWidget(RectWidgetBase):
	def draw(self, screen):
		tryCall(self.overlay, "draw", screen, self)
		WidgetBase.draw(self, screen)
		self.diff = False

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

	def solve(self, basePos: int, baseLength: int, modifier: Callable[[int, int, int], None]):
		'''
		UB if sum of absoluteProportion is bigger then 1.
		UB if size of self.widgetAttribs mismatches size of parent widget array

		parameter `modifier` will be called with arguments (index, pos, length) aka (index, x, width) / (index, y, height)
		'''
		masterProportion: int = sum(i.proportion for i in self.widgetAttribs if i.visible and (not i.absolute)) # the total weight of all widgets
		absoluteConsumption: int = sum(i.proportion for i in self.widgetAttribs if i.visible and i.absolute) * baseLength
		unit: float = (baseLength - absoluteConsumption) / masterProportion if masterProportion > 0 else 0
		
		acc: float = float(basePos)
		orderIndexArray = sorted(range(len(self.widgetAttribs)), key = lambda i: self.widgetAttribs[i].order)
		for i in orderIndexArray:
			if (not self.widgetAttribs[i].visible): continue
			length = self.widgetAttribs[i].proportion * (baseLength if self.widgetAttribs[i].absolute else unit)
			modifier(i, int(round(acc)), int(math.floor(length)))
			acc += length

	def activateSubLayout(self, widgets: list[RectWidgetBase]):
		for i, w in enumerate(widgets):
			if (self.widgetAttribs[i].visible): w.activateLayout()

	# ================ State ================
	
	widgetAttribs: list[LinearLayoutAttribute] = field(default_factory=list)

# ################ Layout ################

# ================ Linear Layout ================
# Horizontal Layout
@dataclass(slots = True)
class RectWidgetHLayout(RectWidgetBase):
	solver: LinearLayoutSolver = field(default_factory=LinearLayoutSolver)

	def modifier_impl(self, i: int, x: int, w: int):
		self.widgets[i].pos.x = x
		self.widgets[i].dim.x = w
	
	def addWidget[T: RectWidgetBase](self, layoutAttrib: LinearLayoutAttribute, widgetType: type[T], **arg) -> T:
		self.solver.addAttrib(layoutAttrib)
		return super().addWidget(widgetType, **arg)

	def activateLayout(self):
		'''recursive'''
		for w in self.widgets:
			w.dim.y = self.dim.y
			w.pos.y = self.pos.y
		self.solver.solve(self.pos.x, self.dim.x, self.modifier_impl)
		self.solver.activateSubLayout(self.widgets)

	def draw(self, screen):
		WidgetBase.draw(self, screen)

# Vertical Layout
@dataclass(slots = True)
class RectWidgetVLayout(RectWidgetBase):
	solver: LinearLayoutSolver = field(default_factory=LinearLayoutSolver)

	def modifier_impl(self, i: int, y: int, h: int):
		self.widgets[i].pos.y = y
		self.widgets[i].dim.y = h
	
	def addWidget[T: RectWidgetBase](self, layoutAttrib: LinearLayoutAttribute, widgetType: type[T], **arg) -> T:
		self.solver.addAttrib(layoutAttrib)
		return super().addWidget(widgetType, **arg)

	def activateLayout(self):
		'''recursive'''
		for w in self.widgets:
			w.dim.x = self.dim.x
			w.pos.x = self.pos.x
		self.solver.solve(self.pos.y, self.dim.y, self.modifier_impl)
		self.solver.activateSubLayout(self.widgets)

	def draw(self, screen):
		WidgetBase.draw(self, screen)

# ================ United Layout ================
'''
Positions in Widgets managed by United Layout has the exception of
being relative to the parent widget, instead of absolute position.
Therefore all widgets using United Layout must only interact with
it's parent, and can only be owned by it's parent.
'''

@dataclass(slots=True)
class UnitedLinearLayoutAttribute:
	# the index of the widget in the layout;
	# positive for start from left; negative for start from right
	order: int = -1
	visible: bool = True

@dataclass(slots=True)
class UnitedLinearLayoutSolver:

	# ================ Public Interface ================

	def addAttrib(self, attrib: UnitedLinearLayoutAttribute):
		self.widgetAttribs.append(attrib)

	def solve(self, basePos: int, baseLength: int, unit: int, getter: Callable[[int], int], modifier: Callable[[int, int, int], None]):
		'''
		UB if size of self.widgetAttribs mismatches size of parent widget array
		Strict exclusivity is not guaranteed.

		parameter `modifier` will be called with arguments (index, pos, length) aka (index, x, width) / (index, y, height)
		'''
		orderIndexArray = sorted(range(len(self.widgetAttribs)), key = lambda i: self.widgetAttribs[i].order)
		positiveBegin: int = 0
		while (positiveBegin < len(self.widgetAttribs) and self.widgetAttribs[orderIndexArray[positiveBegin]].order < 0): positiveBegin += 1

		# negatives
		nacc: int = basePos + baseLength
		for i in range(positiveBegin):
			index = positiveBegin - i - 1
			if (not self.widgetAttribs[orderIndexArray[index]].visible): continue
			adv = getter(orderIndexArray[index]) * unit # advancement
			nacc -= adv
			modifier(orderIndexArray[index], nacc, adv)

		# positives
		pacc: int = basePos
		for i in range(positiveBegin, len(self.widgetAttribs)):
			if (not self.widgetAttribs[orderIndexArray[i]].visible): continue
			adv = getter(orderIndexArray[i]) * unit # advancement
			modifier(orderIndexArray[i], pacc, adv)
			pacc += adv

	def findMinLength(self, getter: Callable[[int], int], unit: int):
		return sum(getter(i) * w.visible for i, w in enumerate(self.widgetAttribs)) * unit

	def activateSubLayout(self, widgets: list[RectWidgetBase]):
		for i, w in enumerate(widgets):
			if (self.widgetAttribs[i].visible): w.activateLayout()


	# ================ State ================
	
	widgetAttribs: list[UnitedLinearLayoutAttribute] = field(default_factory=list)

# Vertical Layout
@dataclass(slots = True)
class RectWidgetUnitedVLayout(RectWidgetBase):
	solver: UnitedLinearLayoutSolver = field(default_factory=UnitedLinearLayoutSolver)

	def modifier_impl(self, i: int, y: int, h: int):
		self.widgets[i].pos.y = y
		self.widgets[i].dim.y = h
	def getter_impl(self, i: int) -> int:
		return self.widgets[i].reportHeight()

	# ================ Contract Interface ================

	def addWidget[T: RectWidgetBase](self, layoutAttrib: UnitedLinearLayoutAttribute, widgetType: type[T], **arg) -> T:
		self.solver.addAttrib(layoutAttrib)
		return super().addWidget(widgetType, **arg)

	def activateLayout(self):
		'''recursive'''
		for w in self.widgets:
			w.dim.x = self.dim.x
			w.pos.x = self.pos.x
		self.solver.activateSubLayout(self.widgets)
		self.dim.y = self.solver.findMinLength(self.getter_impl, self.uniform.unit)
		self.solver.solve(self.pos.y, self.dim.y, self.uniform.unit, self.getter_impl, self.modifier_impl)

	def reportHeight(self): return sum(w.reportHeight() * w.visible() for w in self.widgets)

	def draw(self, screen):
		return WidgetBase.draw(self, screen)


# Vertical Layout
@dataclass(slots = True)
class RectWidgetRigidUnitedVLayout(RectWidgetUnitedVLayout):
	def activateLayout(self):
		'''recursive'''
		for w in self.widgets:
			w.dim.x = self.dim.x
			w.pos.x = self.pos.x
		self.solver.activateSubLayout(self.widgets)
		self.solver.solve(self.pos.y, self.solver.findMinLength(self.getter_impl, self.uniform.unit),
		                  self.uniform.unit, self.getter_impl, self.modifier_impl)

# im not making h layout because lazyness and i don't need it so screw it

# ################ Overlay ################
'''
Overlay are display objects which are attached to widgets as their visual manifest.
Same as widgets, (by convention,) overlays are only constructible by calling
setOverlay method of a rect widget.
The design philosophy of overlays is to be stateless. An overlay object should
as light as possible and are targeted to rely mostly on arguments and temporary
values.
'''

type WidgetTheme = dict[type[RectWidgetBase],
                        type[RectWidgetBase.StyleSheet]]

@dataclass(slots=True)
class OverlayBase:
	# ================ Contract Interface ================
	
	def draw(self, parent: RectWidgetBase): pass

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet:
		margin: int = 0
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

	# ================ State & Global ================

	diff: bool = True
	uniform: Global | None = None

@dataclass(slots=True)
class LabelOverlay(OverlayBase):
	texture: pygame.Surface | None = None

	# ================ Contract Interface ================
	
	def draw(self, screen: pygame.Surface, parent: RectWidgetBase):
		if (self.texture is None): return
		if (self.texture.get_width() >
		    parent.dim.x - (self.styleSheet.margin + parent.styleSheet.margin) * 2 - 
			self.styleSheet.indentation):
			prevClip = screen.get_clip()
			screen.set_clip(prevClip.clip(
				makeMarginedRect(parent.pos, parent.dim, parent.styleSheet.margin + self.styleSheet.margin)))

			screen.blit(self.texture,
			            dest=(parent.pos.x + parent.dim.x - self.styleSheet.margin - self.styleSheet.indentation - self.texture.get_width(),
			                  parent.pos.y + (parent.dim.y - self.styleSheet.margin * 2 -
			                                  self.texture.get_height()) // 2 + self.styleSheet.margin))			
			screen.set_clip(prevClip)
		else:
			screen.blit(self.texture,
			            dest=(parent.pos.x + self.styleSheet.margin + self.styleSheet.indentation
			                  if not self.styleSheet.center else
			                  parent.pos.x + parent.dim.x // 2 - self.texture.get_width() // 2,
			                  parent.pos.y + (parent.dim.y - self.styleSheet.margin * 2 -
			                                  self.texture.get_height()) // 2 + self.styleSheet.margin))
		self.diff = False

	# ================ Public Interface ================

	def setText(self, text: str, width: int = 0) -> int:
		self.texture, height = self.uniform.font.render(
			text, self.styleSheet.fontSize, self.styleSheet.textColor, width)
		self.diff = True
		return height

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(OverlayBase.StyleSheet):
		textColor: Color = DefaultColor
		fontSize: int = 48
		indentation: int = 0
		center: bool = False
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

	def font_impl(self, fontSize):
		return self.uniform.font.font(fontSize)

@dataclass(slots=True)
class IconOverlay(OverlayBase):
	texture: pygame.Surface | None = None

	# ================ Contract Interface ================
	
	def draw(self, screen: pygame.Surface, parent: RectWidgetBase):
		if (self.texture is None): return
		screen.blit(self.texture,
		            dest=(parent.pos.x + self.styleSheet.margin,
		                  parent.pos.y + self.styleSheet.margin))
		self.diff = False

	# ================ Public Interface ================
	
	def setImage(self, texture: pygame.Surface):
		self.texture = texture
		self.diff = True

# ################ Input Handler ################

class InputHandler:

	# ================ Public Interface ================
	
	@staticmethod
	def handle(baseWidget: RectWidgetBase, uniform: Global) -> bool:
		'''
		Return whether the program will continue running
		'''
		for event in pygame.event.get():
			# Preliminary parsing
			match (event.type):
				case pygame.QUIT: return False
				case _:
					if (uniform.widgetState == WidgetState.Normal):
						baseWidget.handleEvent(event)
					if (uniform.widgetState == WidgetState.Focused):
						tryCall(uniform.focusWidget, "handleEvent", event)
			
		return True

# ################ Widgets ################
'''
Widget Instances, who are widgets that are not widget bases, does not exersise
the same convention as widget bases. They are strictly leaf of a widget tree,
and do not have sub-widgets under the normal contract. However, widgets can
have sub widgets maintained directly or indirectly by explicit, manual logic.
'''

@dataclass(slots=True)
class PushButtonWidget(RectWidgetBase):
	'''
	This class also serves as a demo of the Event Handling system
	'''

	onPress: Callable[[], None] | Callable[[Self], None] = lambda: None

	pressing: bool = False

	# ================ Contract Interface ================

	def handleEvent(self, event):
		if (super().handleEvent(event)): return True # process sub widgets
		# sub widgets not handled - attempt handling for this widget
		# along with that, state is also modified
		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				self.state.colorOverride = self.styleSheet.pressColor
				self.pressing = True
				self.diff = True
			case pygame.MOUSEBUTTONUP:
				if (not self.pressing): return
				optionalCall(self.onPress, self)
				self.state.colorOverride = None
				self.pressing = False
				self.diff = True
			case Events.MouseLeave:
				self.state.colorOverride = None
				self.pressing = False
				return False
			case _:	return False
		return True

	# ================ Public Interface ================
	
	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(RectWidgetBase.StyleSheet):
		pressColor: Color = DefaultColor
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class ToggleButtonWidget(RectWidgetBase):
	onPress: Callable[[], None] | Callable[[Self], None] = lambda: None

	pressing: bool = False

	# ================ Contract Interface ================

	def handleEvent(self, event):
		if (super().handleEvent(event)): return True # process sub widgets
		# sub widgets not handled - attempt handling for this widget
		# along with that, state is also modified
		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				if (not self.pressing):
					self.state.colorOverride = self.styleSheet.pressColor
					self.pressing = True
					self.diff = True
				else:
					optionalCall(self.onPress, self)
					self.state.colorOverride = None
					self.pressing = False
					self.diff = True
			case _:	return False
		return True

	# ================ Public Interface ================
	
	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(RectWidgetBase.StyleSheet):
		pressColor: Color = DefaultColor
	styleSheet: StyleSheet = field(default_factory=StyleSheet)


@dataclass(slots=True)
class IconedPushButtonWidget(PushButtonWidget):
	# ================ Contract Interface ================

	def __post_init__(self):
		self.setOverlay(IconOverlay)

	def activateLayout(self):
		self.overlay.styleSheet.margin = self.styleSheet.iconMargin + self.styleSheet.margin
		self.overlay.setImage(pygame.transform.smoothscale(
			self.source, scaleToFit(
				ivec2.fromTuple(self.source.get_size()),
			    self.dim - ivec2(self.overlay.styleSheet.margin,
			                     self.overlay.styleSheet.margin) * 2).toTuple()))

	# ================ Public Interface ================

	source: pygame.Surface | None = None

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(PushButtonWidget.StyleSheet):
		iconMargin: int = 0
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class LabeledPushButtonWidget(PushButtonWidget):
	# ================ Contract Interface ================

	def __post_init__(self):
		self.setOverlay(LabelOverlay).styleSheet.center = True

	def activateLayout(self):
		self.overlay.setText(self.text, self.dim.x)
	
	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(PushButtonWidget.StyleSheet):
		textMargin: int = 0
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

	# ================ Public Interface ================

	text: str = ""

	def setText(self, text: str | None = None) -> int:
		if text is not None: self.text = text
		return self.overlay.setText(self.text, self.dim.x)
	

@dataclass(slots=True)
class ToggleWidget(PushButtonWidget):
	on: bool = False
	onToggle: Callable[[], None] | Callable[[Self], None] = lambda: None

	def toggle(self):
		self.on = not self.on
		self.diff = True
		optionalCall(self.onToggle, self)

	def __post_init__(self):
		self.onPress = self.toggle

	# ================ Contract Interface ================

	def draw(self, screen: pygame.Surface):
		m = self.styleSheet.margin
		x = self.pos.x + m
		y = self.pos.y + m
		w = self.dim.x - m * 2
		h = self.dim.y - m * 2
		if (w <= 0 or h <= 0):
			self.diff = False
			return

		xunit = w / 4
		yunit = h / 2
		color = self.styleSheet.onColor if self.on else self.styleSheet.offColor
		draw.circle(screen, color, (x + xunit, y + yunit), xunit)
		draw.circle(screen, color, (x + xunit * 3, y + yunit), xunit)
		draw.rect(screen, color, (x + xunit, y, xunit * 2, yunit * 2))
		draw.circle(screen, self.styleSheet.nodeColor,
		            (x + xunit * 3, y + yunit) if self.on else (x + xunit, y + yunit),
		            xunit - self.styleSheet.nodePadding)
		self.diff = False

	# ================ Geometry ================

	def activateLayout(self):
		'''
		Applying the constraint of strict 1 : 2 geometry (inner drawable area)
		'''
		m = self.styleSheet.margin
		innerW = self.dim.x - m * 2
		innerH = self.dim.y - m * 2
		if (innerW <= 0 or innerH <= 0): return

		unit = min(innerW / 2, innerH)
		self.dim = ivec2(unit * 2 + m * 2, unit + m * 2)
		self.diff = True

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(PushButtonWidget.StyleSheet):
		onColor: Color = DefaultColor
		offColor: Color = DefaultColor
		nodeColor: Color = DefaultColor
		nodePadding: int = 4

	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class DragWidget(RectWidgetBase):
	onDrag: Callable[[], None] | Callable[[Self], None] = lambda: None

	# ================ State ================

	dragging: bool = False
	prevPos: ivec2 = field(default_factory=lambda: ivec2(0, 0))

	# ================ Contract Interface ================

	def handleEvent(self, event):
		if (not self.dragging and super().handleEvent(event)): return True
		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				self.enterFocus()
				self.state.colorOverride = self.styleSheet.dragColor
				optionalCall(self.onDrag, self)
				self.dragging = True
				return True
			case pygame.MOUSEBUTTONUP:
				if (event.button != 1): return False
				self.exitFocus()
				self.state.colorOverride = None
				optionalCall(self.onDrag, self)
				self.dragging = False
				self.refreshHover(ivec2(event.pos[0], event.pos[1]))
				self.diff = True
				return True
			case pygame.MOUSEMOTION:
				if (self.dragging):
					self.prevPos = self.pos
					self.pos += ivec2(event.rel[0], event.rel[1])
					self.diff = True
					optionalCall(self.onDrag, self)
					return True
			case _:
				return False
		return False

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(RectWidgetBase.StyleSheet):
		dragColor: Color = DefaultColor
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class SliderWidgetBase(RectWidgetBase):
	Axis: ClassVar[int] # 0 for Horizontal, 1 for Vertical
	
	value: float = 0.0 # Linearly traveling between 0.0 and 1.0
	onValueChange: Callable[[], None] | Callable[[Self], None] = lambda: None

	dragger: DragWidget | None = None

	def initDragger_impl(self):
		self.dragger = self.addWidget(DragWidget, onDrag=self.handleDrag_impl)
		self.dragger.styleSheet.roundCornerRadius = self.styleSheet.roundCornerRadius
		self.dragger.styleSheet.backgroundColor = self.styleSheet.draggerNormalColor
		self.dragger.styleSheet.hoverColor = self.styleSheet.draggerHoverColor
		self.dragger.styleSheet.dragColor = self.styleSheet.draggerDragColor
		self.dragger.styleSheet.margin = self.styleSheet.draggerMargin + self.styleSheet.margin

	# ================ Contract Interface ================

	def draw(self, screen):
		pygame.draw.rect(screen, self.styleSheet.backgroundEmptyColor, makeRect(self.pos, self.dim))
		return super().draw(screen)
		
	def handleDrag_impl(self):
		self.dragger.pos[not self.Axis] = self.pos[not self.Axis]
		self.dragger.pos[self.Axis] = clamp(
			self.dragger.pos[self.Axis], self.pos[self.Axis],
			self.pos[self.Axis] + self.dim[self.Axis] - self.dragger.dim[self.Axis])

		self.value = (self.dragger.pos[self.Axis] - self.pos[self.Axis]) / (
			self.dim[self.Axis] - self.dragger.dim[self.Axis])
		self.diff = True

		self.valueChange_impl()

	def handleEvent(self, event):
		if (super().handleEvent(event)): return True
		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				self.dragger.pos[self.Axis] = event.pos[self.Axis] - self.dragger.dim[self.Axis] / 2
				self.dragger.handleEvent(event)
				self.handleDrag_impl()
				self.diff = True
				return True

	def activateLayout(self):
		if (self.dim.y == 0 or self.dim.x == 0): return
		margin: int = self.styleSheet.draggerMargin + self.styleSheet.margin

		if (self.dragger is None): self.initDragger_impl()
		
		self.dragger.pos = ivec2(self.pos.x, self.pos.y)
		self.dragger.dim = ivec2(self.dim.x * (self.draggerPortion if not self.Axis else 1) + (not self.Axis) * margin * 2,
		          			     self.dim.y * (self.draggerPortion if self.Axis else 1) + (self.Axis) * margin * 2)
		SliderWidgetBase.setValue(self, self.value)

	# ================ Public Interface ================

	def setValue(self, value: float):
		self.value = value
		pos = self.pos[self.Axis] + (self.dim[self.Axis] - self.dragger.dim[self.Axis]) * value
		self.dragger.pos[self.Axis] = pos
		self.diff = True
	def getValue(self): return self.value

	def valueChange_impl(self):
		optionalCall(self.onValueChange, self)

	# ================ Style ================

	draggerPortion: float = 0.1

	@dataclass(slots=True)
	class StyleSheet(RectWidgetBase.StyleSheet):
		backgroundEmptyColor: Color = DefaultColor
		draggerNormalColor: Color = DefaultColor
		draggerHoverColor: Color = DefaultColor
		draggerDragColor: Color = DefaultColor
		draggerMargin: float = 0.0
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class SliderHWidget(SliderWidgetBase):
    Axis: ClassVar[int] = 0
@dataclass(slots=True)
class SliderVWidget(SliderWidgetBase):
    Axis: ClassVar[int] = 1

@dataclass(slots=True)
class IntegerSliderWidgetBase(SliderWidgetBase):
	scope: tuple[int, int] = (0, 1)

	def setValue(self, value: int):
		super().setValue((value - self.scope[0]) / (self.scope[1] - self.scope[0]))

	def getValue(self):
		return int(self.scope[0] + super().getValue() * (self.scope[1] - self.scope[0]))

@dataclass(slots=True)
class IntegerSliderHWidget(IntegerSliderWidgetBase):
    Axis: ClassVar[int] = 0
@dataclass(slots=True)
class IntegerSliderVWidget(IntegerSliderWidgetBase):
    Axis: ClassVar[int] = 1


@dataclass(slots=True)
class LabelWidget(TransparentRectWidget):
	# ================ Contract Interface ================

	def __post_init__(self):
		self.setOverlay(LabelOverlay)

	def activateLayout(self):
		self.overlay.setText(self.text)
	
	# ================ Public Interface ================

	text: str = ""

	def setText(self, text: str | None = None) -> int:
		if text is not None: self.text = text
		return self.overlay.setText(self.text)

@dataclass(slots=True)
class IconWidget(TransparentRectWidget):
	# ================ Contract Interface ================

	def __post_init__(self):
		self.setOverlay(IconOverlay)

	def activateLayout(self):
		self.overlay.setImage(pygame.transform.smoothscale(
			self.source, scaleToFit(ivec2.fromTuple(self.source.get_size()), self.dim).toTuple()))

	# ================ Public Interface ================

	source: pygame.Surface | None = None

	def setImage(self, path: str):
		self.source = loadIcon(path)
		self.activateLayout()

@dataclass(slots=True)
class LineEditWidget(RectWidgetBase):
	text: str = ""
	cursor: int = 0

	onEdit:         Callable[[], None] | Callable[[Self], None] = lambda: None
	onEditComplete: Callable[[], None] | Callable[[Self], None] = lambda: None

	# ================ Contract Interface ================

	def draw(self, screen):
		super().draw(screen)

		# draw cursor
		if (not self.state.hover): return
		pygame.draw.rect(screen, self.styleSheet.cursorColor, makeRect(
			self.pos + ivec2(
				min(self.dim.x - self.styleSheet.textIndentation, self.styleSheet.textIndentation + 
				self.uniform.font.findWidth(self.text[:self.cursor], self.overlay.styleSheet.fontSize)),
				int(self.styleSheet.margin * 1.5)),
			ivec2(self.styleSheet.cursorWidth, self.dim.y - 3 * self.styleSheet.margin)
		))

	def __post_init__(self):
		label = self.setOverlay(LabelOverlay)
		label.styleSheet.fontSize = int(self.uniform.fontSize * 0.6)
		label.styleSheet.indentation = self.styleSheet.textIndentation
		label.styleSheet.textColor = self.styleSheet.textColor
		label.setText(self.text)

	def isEditing_impl(self):
		return (self.uniform.widgetState == WidgetState.Focused) and (self.uniform.focusWidget is self)
	def handleEvent(self, event):
		if (super().handleEvent(event)): return True

		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				if (inRange(makeRect(self.pos, self.dim), ivec2.fromTuple(event.pos))):
					self.enterFocus()
					self.state.colorOverride = self.styleSheet.editColor
					self.diff = True
				else: self.exit_impl()
			case pygame.TEXTINPUT:
				if (not self.isEditing_impl()): return False
				self.text = self.text[:self.cursor] + event.text + self.text[self.cursor:]
				self.cursor += 1
				self.updateText_impl()
			case pygame.KEYDOWN:
				if (not self.isEditing_impl()): return False
				match (event.key):
					case pygame.K_ESCAPE | pygame.K_RETURN:
						self.exit_impl()
					case pygame.K_BACKSPACE:
						if (self.cursor == 0): return False
						self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
						self.cursor -= 1
						self.updateText_impl()
					case pygame.K_DELETE:
						if (self.cursor == len(self.text)): return False
						self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
						self.updateText_impl()
					case pygame.K_LEFT:
						self.cursor = max(0, self.cursor - 1)
						self.diff = True
					case pygame.K_RIGHT:
						self.cursor = min(len(self.text), self.cursor + 1)
						self.diff = True

	def updateText_impl(self):
		optionalCall(self.onEdit, self)
		self.overlay.setText(self.text)

	def exit_impl(self):
		self.state.colorOverride = None
		optionalCall(self.onEditComplete, self)
		self.exitFocus()

	# ================ Public Interface ================

	def setText(self, text: str):
		self.text = text
		self.overlay.setText(self.text)
		self.cursor = len(text)

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(RectWidgetBase.StyleSheet):
		editColor: Color = DefaultColor
		textIndentation: int = 0
		cursorWidth: int = 2
		cursorColor: Color = DefaultColor
		textColor: Color = DefaultColor
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class IntegerLineEditWidget(LineEditWidget):
	text: str = "0"
	cursor: int = 1

	value: int = 0
	scope: tuple[int, int] | None = None

	# ================ Public Interface ================

	def getValue(self): return self.value
	def setValue(self, value: int):
		self.value = int(value)
		self.setText(str(value))

	# ================ Logical Implementation ================

	def regulateText_impl(self) -> bool:
		try:
			self.value = int(self.text)
		except ValueError:
			return False

		if (self.scope is not None):
			old = self.value
			self.value = int(clamp(self.value, self.scope[0], self.scope[1]))
			if (old != self.value):
				self.text = str(self.value)
				self.updateText_impl()
		return True

	lastText: str = "0"
	def exit_impl(self):
		if (self.regulateText_impl()):
			optionalCall(self.onEditComplete, self)
		else: self.text = self.lastText
		self.lastText = self.text
		self.updateText_impl()
		self.state.colorOverride = None
		self.exitFocus()


@dataclass(slots=True, kw_only=True)
class IntegerFieldWidget(RectWidgetHLayout):
	scope: InitVar[tuple[int, int]]
	
	onValueChange: Callable[[], None] | Callable[[Self], None] = lambda: None
	value: int = 0
	
	edit:  IntegerLineEditWidget | None = field(init=False, default=None)
	slider: IntegerSliderHWidget | None = field(init=False, default=None)

	def syncValueFromSlider_impl(self):
		self.edit.setValue(self.slider.getValue())
		self.value = self.slider.getValue()
		optionalCall(self.onValueChange, self)
	def syncValueFromEdit_impl(self):
		self.slider.setValue(self.edit.getValue())
		self.value = self.edit.getValue()
		optionalCall(self.onValueChange, self)

	# ================ Public Interface ================
	
	def setValue(self, value: int):
		self.value = value
		self.edit.setValue(value)
		self.slider.setValue(value)

	# ================ Contract Interface ================
	
	def __post_init__(self, scope: tuple[int, int]):
		self.edit   = self.addWidget(
			LinearLayoutAttribute(0, self.styleSheet.editPortion),
			IntegerLineEditWidget, scope=scope,
			onEditComplete=self.syncValueFromEdit_impl)
		self.slider = self.addWidget(
			LinearLayoutAttribute(1, self.styleSheet.sliderPortion),
			IntegerSliderHWidget, scope=scope,
			onValueChange=self.syncValueFromSlider_impl)

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(RectWidgetHLayout.StyleSheet):
		editPortion: int = 1
		sliderPortion: int = 1
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class ConfirmationWidget(RectWidgetHLayout):
	confirmed: bool | None = None

	onAction: Callable[[], None] | Callable[[Self], None] = lambda: None

	def handleConfirm_impl(self): self.confirmed = True; optionalCall(self.onAction, self)
	def handleCancel_impl(self): self.confirmed = False; optionalCall(self.onAction, self)

	# ================ Contract Interface ================

	def draw(self, screen):
		WidgetBase.draw(self, screen)

	def __post_init__(self):
		t = self.addWidget(LinearLayoutAttribute(order=0), LabeledPushButtonWidget, onPress=self.handleCancel_impl,  text="Cancel")
		t.styleSheet = replace(self.styleSheet)
		t.overlay.styleSheet.fontSize = int(self.uniform.fontSize * 0.7)
		f = self.addWidget(LinearLayoutAttribute(order=1), LabeledPushButtonWidget, onPress=self.handleConfirm_impl, text="Confirm")
		f.styleSheet = replace(self.styleSheet)
		f.overlay.styleSheet.fontSize = int(self.uniform.fontSize * 0.7)

	def reportHeight(self):
		return 2

	def activateLayout(self):
		if (self.dim.y == 0): return
		super().activateLayout()

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(LabeledPushButtonWidget.StyleSheet): pass
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class ScrollLayout(RectWidgetRigidUnitedVLayout):
	# ================ Contract Interface ================

	def draw(self, screen: pygame.Surface):
		'''
		Draw within range.
		'''
		prevClip = screen.get_clip()
		screen.set_clip(makeRect(self.pos, self.dim))
		
		#RectWidgetBase.draw(self, screen)
		super().draw(screen)

		screen.set_clip(prevClip)

	def handleEvent(self, event):
		if (super().handleEvent(event)): return True

		match (event.type):
			case pygame.MOUSEBUTTONDOWN | pygame.MOUSEBUTTONUP:
				match (event.button):
					case 4:  # Scroll Up
						diff: int = self.pos.y - min(w.pos.y for w in self.widgets if w.visible())
						if (diff > 0):
							for w in self.widgets:
								w.move(ivec2(0, min(self.styleSheet.scrollVel, diff)))
								w.subWidgetHandleMouseDisplacement(ivec2.fromTuple(pygame.mouse.get_pos()))
							self.diff = True
					case 5:  # Scroll Down
						diff: int = max(w.pos.y + w.dim.y for w in self.widgets if w.visible()) - (self.pos.y + self.dim.y)
						if (diff > 0):
							for w in self.widgets:
								w.move(ivec2(0, -min(self.styleSheet.scrollVel, diff)))
								w.subWidgetHandleMouseDisplacement(ivec2.fromTuple(pygame.mouse.get_pos()))
							self.diff = True

	@dataclass(slots=True)
	class StyleSheet(RectWidgetUnitedVLayout.StyleSheet):
		scrollVel: int = 10
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

	# ================ Public Interface ================

	def scrollToWidget(self, widget: RectWidgetBase):
		'''widget must be sub widget of this layout.'''
		diff = self.pos.y - widget.pos.y
		for w in self.widgets:
			w.move(ivec2(0, diff))
			w.subWidgetHandleMouseDisplacement(ivec2.fromTuple(pygame.mouse.get_pos()))
		self.diff = True

	def resetScroll(self):
		self.scrollToWidget(self.widgets[0])

@dataclass(slots=True)
class RectWidgetHolder(RectWidgetBase):
	content: RectWidgetBase | None = None
	
	# ================ Contract Interface ================

	def activateLayout(self):
		if (self.dim.y == 0): return
		self.content.pos = replace(self.pos)
		self.content.dim = replace(self.dim)
		super().activateLayout()
