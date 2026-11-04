# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from . import rgb
import pygame
import time

class Framework:
	def __init__(self, updateFunc, renderFunc):
		self.update = updateFunc
		self.render = renderFunc

		self.TickInterval = 16666667
		self.StatInterval = 1_000_000_000

	def run(self):
		last = time.perf_counter_ns()
		lastStat = time.perf_counter_ns()
		accumulator = int(0)
		fps = 0
		ups = 0

		while(True):
			while (accumulator >= self.TickInterval):
				if (not self.update()):
					self.quit()
					return
				accumulator -= self.TickInterval
				ups += 1

			#self.screen.fill(rgb.MikuColor)
			self.render()
			fps += 1
			
			now = time.perf_counter_ns()
			accumulator += now - last
			last = now

			if((now - lastStat) >= 1_000_000_000):
				print(f"FPS: {fps} | UPS: {ups}")
				fps = 0
				ups = 0
				lastStat = now
			
			pygame.display.flip()

	def quit(self):
		pygame.quit()
