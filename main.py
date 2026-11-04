import tx
import math
import random
import pygame
pygame.init()



engine = tx.WidgetEngine(tx.ivec2(800, 600), tx.RectWidgetHLayout)
base = engine.base()
w1 = base.addWidget(tx.RectWidgetBase(pos = tx.ivec2(0, 0), dim = tx.ivec2(0, 0)), tx.LinearLayoutAttribute(proportion=0.5, absolute=True))
w1.style.backgroundColor = tx.rgb.MikuColorEnd
w1.style.roundCornerRadius = 20
w2 = base.addWidget(tx.RectWidgetBase(pos = tx.ivec2(0, 0), dim = tx.ivec2(0, 0)), tx.LinearLayoutAttribute(proportion=2, absolute=False))
w2.style.backgroundColor = tx.rgb.MikuColor
w2.style.roundCornerRadius = 20
w3 = base.addWidget(tx.RectWidgetBase(pos = tx.ivec2(0, 0), dim = tx.ivec2(0, 0)), tx.LinearLayoutAttribute())
w3.style.backgroundColor = tx.rgb.Red
w3.style.roundCornerRadius = 20

base.activateLayout()

def update():
	engine.update()
	return not any(event.type == pygame.QUIT for event in pygame.event.get())
def render():
	engine.render()

framework = tx.Framework(update, render)
framework.run()