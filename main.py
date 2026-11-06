# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

import tx
import math
import random
import pygame
pygame.init()

from dataclasses import replace

theme: tx.WidgetTheme = {
	tx.RectWidgetBase: tx.RectWidgetBase.StyleSheet(
		backgroundColor=tx.MikuColorBegin, roundCornerRadius=20, margin=0),
	tx.RectWidgetHLayout: tx.RectWidgetHLayout.StyleSheet(
		backgroundColor=tx.MikuColorBegin, roundCornerRadius=20, margin=0),
	tx.RectWidgetVLayout: tx.RectWidgetVLayout.StyleSheet(
		backgroundColor=tx.MikuColorBegin, roundCornerRadius=20, margin=0),
	tx.PushButtonWidget: tx.PushButtonWidget.StyleSheet(
		backgroundColor=tx.Blue, roundCornerRadius=20, margin=10),
	tx.ToggleWidget: tx.ToggleWidget.StyleSheet(
		onColor=tx.Blue, offColor=tx.LightGray, nodeColor=tx.White),
	tx.DragWidget: tx.DragWidget.StyleSheet(
		backgroundColor=tx.Blue, roundCornerRadius=20, margin=10),
	tx.SliderHWidget: tx.SliderHWidget.StyleSheet(
		backgroundColor=tx.MikuColorBegin, hoverColor=tx.White,
		draggerNormalColor=tx.LightBlue, draggerHoverColor=tx.Red, draggerDragColor=tx.Blue,
		draggerMargin=0.1)
}



engine = tx.WidgetEngine(tx.ivec2(800, 600), tx.RectWidgetHLayout, theme)
base = engine.base()
base.styleSheet = tx.RectWidgetHLayout.StyleSheet(backgroundColor=tx.Black)

w1 = base.addWidget(tx.LinearLayoutAttribute(proportion=0.5, absolute=True), tx.RectWidgetVLayout)

def onPush():
	if (w2.visible()):
		w2.hide()
	else: w2.show()
	print("button pressed")

b1 = w1.addWidget(tx.LinearLayoutAttribute(proportion=0.5, absolute=True), tx.PushButtonWidget, onPress=onPush)

def onSlide(slider: tx.SliderHWidget):
	print(slider.value)

s1 = w1.addWidget(tx.LinearLayoutAttribute(), tx.SliderHWidget, onValueChange=onSlide)

w2 = base.addWidget(tx.LinearLayoutAttribute(proportion=2, absolute=False), tx.RectWidgetBase)
w3 = base.addWidget(tx.LinearLayoutAttribute(), tx.DragWidget)

base.activateLayout()

def update() -> bool:
	return engine.update()
def render():
	engine.render()

framework = tx.Framework(update, render)
framework.run()