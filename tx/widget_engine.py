# Inspired by: Qt

from geometry import *
from rgb import *
from typing import Protocol

class WidgetConcept(Protocol):
	def update() -> None:
		...

	def draw(renderer) -> None:
		...

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
		w.update()
		w.draw(renderer)
	}
	'''
	def __init__(self):
		self.m_widgets = []
		pass

	# ================ Public Interface ================

	def addWidget(self, widget) -> int:
		self.m_widgets.append(widget)
		return len(self.m_widgets) - 1

	def widget(self, index: int) -> WidgetBase:
		return self.m_widgets[index]
		
class RectWidgetBase(WidgetBase):
	def __init__(self, topLeft: ivec2, width: int, height: int):
		super().__init__()
		self.m_dimension = Rect(topLeft, width, height)
		self.m_color = White

	# ================ Main Loop Interface ================

	def draw(self, renderer):
		renderer.drawRect(self.m_dimension, self.m_color)
		
	def update(self):
		pass

	# ================ Public Interface ================


	# ================ Styling ================

	#class StyleSheet:
		