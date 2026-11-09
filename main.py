# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

import src
import math
import random
import pygame
pygame.init()

from dataclasses import replace

class WidgetEngine[T: src.RectWidgetBase]:
	'''
	Highest level wrapper of the widget system
	'''

	def __init__(self, windowDimension: src.ivec2, BaseWidgetType: type[T], theme: src.WidgetTheme):
		self.screen = pygame.display.set_mode((windowDimension.x, windowDimension.y))
		self.baseWidget = BaseWidgetType(
			uniform=self.uniform,
			dim=windowDimension, theme=theme, styleSheet = replace(theme[BaseWidgetType]))
		
	# ================ Contract Interface ================

	def base(self) -> T:
		return self.baseWidget

	def render(self):
		self.baseWidget.render(self.screen)

	def update(self) -> bool:
		self.baseWidget.update()
		return src.InputHandler.handle(self.baseWidget, self.uniform)

	# ================ Global ================

	uniform: src.Global = src.Global()



def widgetDebug():
	engine = WidgetEngine(src.ivec2(800, 600), src.RectWidgetHLayout, src.theme)
	base = engine.base()
	base.styleSheet = src.RectWidgetHLayout.StyleSheet(backgroundColor=src.Black)

	w1 = base.addWidget(src.LinearLayoutAttribute(proportion=0.5, absolute=True), src.RectWidgetVLayout)

	def onPush():
		s1.setValue(0.0)

	b1 = w1.addWidget(src.LinearLayoutAttribute(proportion=0.5, absolute=True), src.PushButtonWidget, onPress=onPush)

	def onSlide(slider: src.SliderHWidget):
		print(slider.value)

	s1 = w1.addWidget(src.LinearLayoutAttribute(), src.SliderHWidget, onValueChange=onSlide)

	w2 = base.addWidget(src.LinearLayoutAttribute(proportion=2, absolute=False), src.IconWidget)
	w2.setImage("/home/TX_Jerry/chen.bmp")

	w3 = base.addWidget(src.LinearLayoutAttribute(), src.DragWidget)

	base.activateLayout()

	def update() -> bool:
		return engine.update()
	def render():
		engine.render()

	framework = src.Framework(update, render)
	framework.run()

def engineDebug():
	engine = WidgetEngine(src.ivec2(800, 600), src.RectWidgetHLayout, src.theme)
	base = engine.base()
	canvasw = base.addWidget(src.LinearLayoutAttribute(), src.CanvasWidget)

	base.activateLayout()

	def update() -> bool:
		return engine.update()
	def render():
		engine.render()

	framework = src.Framework(update, render)
	framework.run()

def appDebug():
	engine = WidgetEngine(src.ivec2(1600, 900), src.ApplicationWidget, src.theme)

	engine.base().activateLayout()

	def update() -> bool:
		return engine.update()
	def render():
		engine.render()

	framework = src.Framework(update, render)
	framework.run()

appDebug()
#widgetDebug()