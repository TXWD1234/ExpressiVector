from .rgb import *
from .geometry import *
from pygame import draw, typing

class Renderer:
	def __init__(self, screen):
		self.m_screen = screen
		pass

	def drawRect(self, rect: Rect, color = White):
		draw.rect(self.m_screen, color, rect.toPygameRect())
	def drawRectFrame(self, rect: Rect, width: int, color = White):
		draw.rect(self.m_screen, color, rect.toPygameRect(), width=width)
	def drawRectCornerRounded(self, rect: Rect, radius: int, color = White):
		draw.rect(self.m_screen, color, rect.toPygameRect(), border_radius=radius)

	def drawLine(self, pa: vec2, pb: vec2, color = White):
		draw.line(self.m_screen, color, )