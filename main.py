import tx
import math
import random
import pygame
pygame.init()



engine = tx.WidgetEngine(tx.ivec2(800, 600))
base = engine.base()
w1 = base.addWidget(tx.RectWidgetBase(pos = tx.ivec2(10, 10), dim = tx.ivec2(100, 100)))
w1.style.backgroundColor = tx.rgb.Red
w1.style.roundCornerRadius = 20

def update():
	engine.update()
	return not any(event.type == pygame.QUIT for event in pygame.event.get())
def render():
	engine.render()

framework = tx.Framework(update, render)
framework.run()