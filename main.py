# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

import tx
import math
import random
import pygame
pygame.init()

from dataclasses import replace


engine = tx.WidgetEngine(tx.ivec2(800, 600), tx.RectWidgetHLayout)
base = engine.base()
w1 = base.addWidget(tx.RectWidgetVLayout(), tx.LinearLayoutAttribute(proportion=0.5, absolute=True))
w1.style.backgroundColor = tx.rgb.MikuColorEnd
w1.style.roundCornerRadius = 20

def onPush(button: tx.PushButtonWidget):
	if (w2.visible()):
		w2.hide()
	else: w2.show()
	print("button pressed")

b1 = w1.addWidget(tx.PushButtonWidget(onPress=onPush), tx.LinearLayoutAttribute(proportion=0.5, absolute=True))
b1.setStyleSheet(lambda s: replace(s, backgroundColor = tx.Purple, margin = 10, roundCornerRadius = 20))

w2 = base.addWidget(tx.RectWidgetBase(), tx.LinearLayoutAttribute(proportion=2, absolute=False))
w2.style.backgroundColor = tx.rgb.MikuColor
w2.style.roundCornerRadius = 20
w3 = base.addWidget(tx.RectWidgetBase(), tx.LinearLayoutAttribute())
w3.style.backgroundColor = tx.rgb.Red
w3.style.roundCornerRadius = 20

base.activateLayout()

def update() -> bool:
	return engine.update()
def render():
	engine.render()

framework = tx.Framework(update, render)
framework.run()