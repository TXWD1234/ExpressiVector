from . import rgb
import pygame
import time

class Framework:
	def __init__(self, windowDimension, updateFunc, renderFunc):
		self.update = updateFunc
		self.render = renderFunc
		pygame.init()
		self.screen = pygame.display.set_mode(windowDimension)
		pygame.display.set_caption("TXProject")

		self.TickInterval = 16666667
		self.StatInterval = 1_000_000_000

	def run(self):
		last = time.perf_counter_ns()
		lastStat = time.perf_counter_ns()
		accumulator = int(0)
		fps = 0
		ups = 0

		running = True
		while(running):
			while (accumulator >= self.TickInterval):
				self.update()
				accumulator -= self.TickInterval
				ups += 1

			running = not any(event.type == pygame.QUIT for event in pygame.event.get())

			self.screen.fill(rgb.MikuColor)
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

		pygame.quit()
