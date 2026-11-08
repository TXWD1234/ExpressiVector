# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .geometry import *
from .rgb import *
from .infrastructure import *
from typing import Callable, Generic, TypeVar, Self, Any, ClassVar
import pygame
from dataclasses import dataclass, field, replace

'''
Expressive Vector Image Engine

--- Coordinate System ---
The coordinate in the canvas is relative to the size of the canvas, in the unit
of pixels.
Note that the unit pixels are not actual pixels of the canvas, but the canvas at
1.0 scale. After all the coordinates are just virtual values anyways, choosing
pixels over NDC here is only for implementation convenience, but inherently it's
still continuous coordinates.
The unit in the engine is defined as: Engine Canvas Virtual Pixel Coordinate, or
Canvas VP Coordinate / vpc.

Engine Lifetime
One engine instance manages one document.
'''

@dataclass(slots=True)
class Engine:
	# ================ Camera System ================
	
	@dataclass(slots=True)
	class CanvasState:
		# dim is the real dimension of the canvas in vp coordinates
		#dim: ivec2 = field(default_factory=lambda: ivec2(1920, 1080))
		dim: vec2 = field(default_factory=lambda: vec2(322, 322))
	canvasState: CanvasState = field(default_factory=CanvasState)


	# ================ Canvas Cache ================
	'''
	Caching the visual display of the current data.
	Incremental draw (done in editing functions) for editing, full redraw for
	scaling.
	'''

	@dataclass(slots=True)
	class CanvasCache:
		scale: float
		# canvas is in the unit of scale, which is currently displaying in the
		# canvas widget
		canvas: pygame.Surface

	canvasCache: CanvasCache | None = None

	# full redraw
	def redraw(self, scale: float) -> pygame.Surface:
		self.canvasCache = self.CanvasCache(
			scale, pygame.Surface((self.canvasState.dim * scale).toIvec2().toTuple(), pygame.SRCALPHA))
		self.render_impl(self.canvasCache.canvas, scale)
		return self.canvasCache.canvas

	# ================ Implementation Utility ================

	@staticmethod
	def scalePos_impl(pos: vec2, scale: float) -> tuple[int, int]:
		return (pos * scale).toIvec2().toTuple()

	# ================ Tools ================
	'''
	Contract Interface Convention:
	Each tool must possess the following contract interface:
	- <name>Render(canvas, scale) # for full redraw

	Additionally, each tool should provide at least one public interface to
	perform actions with the tool.
	
	Naming Convention:
	Each tool name everything associated with the tool as:
	`<name>Function`
	
	More specifically, the data of the object associated with the tool should
	be named as `<name>Data`.
	'''

	# ---------------- Unicircle (Debug Purpose) ----------------

	circle: vec2 | None = None

	def drawCircle(self, pos: vec2):
		self.circle = pos
		pygame.draw.circle(self.canvasCache.canvas, White, (self.circle * self.canvasCache.scale).toTuple(), 64 * self.canvasCache.scale)
	
	# ---------------- Stroke ----------------

	@dataclass(slots=True)
	class StrokeObject:
		vertices: list[vec2] = field(default_factory=list)
		color: Color = Black
		width: float = 16

	strokeData: list[StrokeObject] = field(default_factory=list)

	# public interface
	def strokeCreate(self, initPos: vec2, color: Color, width: float):
		self.strokeData.append(self.StrokeObject(vertices=[initPos], color=color, width=width))
		pygame.draw.circle(self.canvasCache.canvas, color,
			Engine.scalePos_impl(initPos, self.canvasCache.scale), (width / 2 * self.canvasCache.scale))

	def strokeAppend(self, pos: vec2):
		self.strokeData[-1].vertices.append(pos)
		Engine.strokeDrawSingleAppend_impl(
			self.canvasCache.canvas, self.canvasCache.scale,
			self.strokeData[-1].vertices[-2], pos,
			self.strokeData[-1].color, self.strokeData[-1].width
		)

	# rendering
	def strokeRender(self, canvas: pygame.Surface, scale: float):
		for obj in self.strokeData: Engine.strokeDrawSingle_impl(canvas, scale, obj)
	@staticmethod
	def strokeDrawSingle_impl(canvas: pygame.Surface, scale: float, object: StrokeObject):
		pygame.draw.circle(canvas, object.color,
			Engine.scalePos_impl(object.vertices[0], scale), int(object.width / 2 * scale))
		for i in range(len(object.vertices) - 1):
			Engine.strokeDrawSingleAppend_impl(
				canvas, scale,object.vertices[i], object.vertices[i + 1],
				object.color, object.width)

	@staticmethod
	def strokeDrawSingleAppend_impl(
		canvas: pygame.Surface, scale: float,
		v1: vec2, v2: vec2, color: Color, width: float):

		diff = v2 - v1
		pygame.draw.polygon(canvas, color, [
			Engine.scalePos_impl(v1 + normalize( leftPerp(diff)) * width * 0.5, scale),
			Engine.scalePos_impl(v1 + normalize(rightPerp(diff)) * width * 0.5, scale),
			Engine.scalePos_impl(v2 + normalize(rightPerp(diff)) * width * 0.5, scale),
			Engine.scalePos_impl(v2 + normalize( leftPerp(diff)) * width * 0.5, scale)
		])

		pygame.draw.circle(canvas, color,
			Engine.scalePos_impl(v2, scale), int(width / 2 * scale))
		
		
	
					

	# ================ Master Rendering ================

	def render_impl(self, canvas: pygame.Surface, scale: float):
		canvas.blit(pygame.transform.scale(pygame.image.load("/home/TX_Jerry/chen.bmp").convert(), canvas.get_size()))
		if (self.circle is not None):
			pygame.draw.circle(canvas, White, (self.circle * scale).toTuple(), 64 * self.canvasCache.scale)