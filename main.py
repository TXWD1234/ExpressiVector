# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

import tx
import math
import random
import pygame
pygame.init()

from dataclasses import replace

class WidgetEngine[T: tx.RectWidgetBase]:
	'''
	Highest level wrapper of the widget system
	'''

	def __init__(self, windowDimension: tx.ivec2, BaseWidgetType: type[T], theme: tx.WidgetTheme):
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
		return tx.InputHandler.handle(self.baseWidget, self.uniform)

	# ================ Global ================

	uniform: tx.Global = tx.Global()



def widgetDebug():
	engine = WidgetEngine(tx.ivec2(800, 600), tx.RectWidgetHLayout, tx.theme)
	base = engine.base()
	base.styleSheet = tx.RectWidgetHLayout.StyleSheet(backgroundColor=tx.Black)

	w1 = base.addWidget(tx.LinearLayoutAttribute(proportion=0.5, absolute=True), tx.RectWidgetVLayout)

	def onPush():
		s1.setValue(0.0)

	b1 = w1.addWidget(tx.LinearLayoutAttribute(proportion=0.5, absolute=True), tx.PushButtonWidget, onPress=onPush)

	def onSlide(slider: tx.SliderHWidget):
		print(slider.value)

	s1 = w1.addWidget(tx.LinearLayoutAttribute(), tx.SliderHWidget, onValueChange=onSlide)

	w2 = base.addWidget(tx.LinearLayoutAttribute(proportion=2, absolute=False), tx.IconWidget)
	w2.setImage("/home/TX_Jerry/chen.bmp")

	w3 = base.addWidget(tx.LinearLayoutAttribute(), tx.DragWidget)

	base.activateLayout()

	def update() -> bool:
		return engine.update()
	def render():
		engine.render()

	framework = tx.Framework(update, render)
	framework.run()

def engineDebug():
	engine = WidgetEngine(tx.ivec2(800, 600), tx.RectWidgetHLayout, tx.theme)
	base = engine.base()
	canvasw = base.addWidget(tx.LinearLayoutAttribute(), tx.CanvasWidget)

	base.activateLayout()

	def update() -> bool:
		return engine.update()
	def render():
		engine.render()

	framework = tx.Framework(update, render)
	framework.run()

def appDebug():
	engine = WidgetEngine(tx.ivec2(1600, 900), tx.ApplicationWidget, tx.theme)

	engine.base().activateLayout()

	def update() -> bool:
		return engine.update()
	def render():
		engine.render()

	framework = tx.Framework(update, render)
	framework.run()

appDebug()