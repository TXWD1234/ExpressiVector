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
		onColor=tx.Blue, offColor=tx.LightGray, nodeColor=tx.White, nodePadding=4),
	tx.DragWidget: tx.DragWidget.StyleSheet(
		backgroundColor=tx.Blue, roundCornerRadius=20, margin=10),
	tx.SliderHWidget: tx.SliderWidgetBase.StyleSheet(
		backgroundColor=tx.MikuColorBegin, hoverColor=tx.White,
		draggerNormalColor=tx.LightBlue, draggerHoverColor=tx.Red, draggerDragColor=tx.Blue,
		draggerMargin=4, roundCornerRadius=20, margin=10),
	tx.SliderVWidget: tx.SliderWidgetBase.StyleSheet(
		backgroundColor=tx.MikuColorBegin, hoverColor=tx.White,
		draggerNormalColor=tx.LightBlue, draggerHoverColor=tx.Red, draggerDragColor=tx.Blue,
		draggerMargin=4, roundCornerRadius=20, margin=10),
	tx.LabelOverlay: tx.LabelOverlay.StyleSheet(
		margin=10, textColor=tx.White, fontSize=64),
	tx.LabelWidget: tx.LabelWidget.StyleSheet(
		backgroundColor=tx.MikuColorBegin, roundCornerRadius=20, margin=0),
	tx.IconOverlay: tx.IconOverlay.StyleSheet(
		margin=0),
	tx.IconWidget: tx.IconWidget.StyleSheet(
		backgroundColor=tx.MikuColorBegin, roundCornerRadius=20, margin=0),
}



engine = tx.WidgetEngine(tx.ivec2(800, 600), tx.RectWidgetHLayout, theme)
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