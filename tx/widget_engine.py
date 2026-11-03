# Inspired by: Qt

from .geometry import *
from .rgb import *
from typing import Protocol
from pygame import draw
from dataclasses import dataclass, field	

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

	def init():
		pass

	widgets: list[WidgetBase] = field(default_factory=list)

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

	def addWidget[T: WidgetBase](self, widget: T) -> T:
		self.widgets.append(widget)
		return self.widgets[-1]

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
		return super().addWidget(widget)

	# ================ Geometry ================

	pos: ivec2 = field(default_factory=lambda: ivec2(0, 0)) # position (topLeft)
	dim: ivec2 = field(default_factory=lambda: ivec2(0, 0)) # dimension

	# ================ Styling ================

	@dataclass(slots=True)
	class StyleSheet:
		backgroundColor: tuple[int, int, int] = Black
		roundCornerRadius: int = 0

	style: StyleSheet = field(default_factory=StyleSheet)



class WidgetEngine:
	def __init__(self, windowDimension: ivec2):
		self.screen = self.screen = pygame.display.set_mode((windowDimension.x, windowDimension.y))
		self.baseWidget = RectWidgetBase(dim = windowDimension)

	def base(self) -> RectWidgetBase:
		return self.baseWidget

	def render(self):
		self.baseWidget.render(self.screen)

	def update(self):
		self.baseWidget.update()