# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .geometry import *
from .rgb import *
from .infrastructure import *
import pygame
from dataclasses import dataclass, field, replace
from typing import Callable

# ================================================================
# **************** Expressive Vector Image Engine ****************
# ================================================================
'''
--- Coordinate System ---
The coordinate in the canvas is relative to the size of the canvas, in the unit
of pixels.
Note that the unit pixels are not actual pixels of the canvas, but the canvas at
1.0 scale. After all the coordinates are just virtual values anyways, choosing
pixels over NDC here is only for implementation convenience, but inherently it's
still continuous coordinates.
The unit in the engine is defined as: Engine Canvas Virtual Pixel Coordinate, or
Canvas VP Coordinate / vpc.

--- Engine Lifetime ---
One engine instance manages one document.
'''

@dataclass(slots=True)
class Engine:
	def __post_init__(self):
		self.initBufferList()
	
	# ================ Camera System ================
	
	@dataclass(slots=True)
	class CanvasState:
		# dim is the real dimension of the canvas in vp coordinates
		dim: vec2 = field(default_factory=lambda: vec2(800, 600))
		#dim: vec2 = field(default_factory=lambda: vec2(322, 322))
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
	#def redraw(self, scale: float) -> pygame.Surface:
	#	scaleFactor = 1.5
	#	scale *= scaleFactor
	#	self.canvasCache = self.CanvasCache(
	#		scale, pygame.Surface((self.canvasState.dim * scale).toIvec2().toTuple(), pygame.SRCALPHA))
	#	self.render_impl(self.canvasCache.canvas, scale)
	#	self.canvasCache.canvas = pygame.transform.smoothscale(self.canvasCache.canvas, (self.canvasState.dim * scale / scaleFactor).toIvec2().toTuple())
	#	return self.canvasCache.canvas

	viewProvider: Callable[[], pygame.Surface] | None = None
	'''
	When a tool has a preview method, and is currently in focused editing state,
	viewProvider can be assigned to provide preview for the canvas.
	'''

	def view(self) -> pygame.Surface:
		if (self.viewProvider is not None): return self.viewProvider()
		return self.canvasCache.canvas

	# ================ Implementation Utility ================

	@staticmethod
	def scaleDist_impl(dist: float, scale: float) -> int:
		return int(math.floor(dist * scale))

	@staticmethod
	def scalePos_impl(pos: vec2, scale: float) -> tuple[int, int]:
		return (pos * scale).toIvec2().toTuple()

	# ================ Object Sequence ================
	'''
	Using indices here instead of direct pointers for the ability to save to
	file.
	
	typeIndex:
	Each tool has a dedicted ID. Their buffer will register in a centralized
	list of buffers to be accessed via index directly
	'''

	bufferList: list[list] = field(default_factory=list)

	def initBufferList(self):
		self.bufferList.append(self.strokeData)
		self.bufferList.append(self.rectData)

	@dataclass(slots=True)
	class ObjectIndex:
		typeIndex: int = 0
		index: int = 0

	objectSequence: list[ObjectIndex] = field(default_factory=list)

	# ================ Tools ================
	'''
	Contract Interface Convention:
	Each tool must possess the following contract interface:
	- <name>Object.render(canvas, scale) # for full redraw

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
	class StrokeConfig:
		color: Color = Black
		width: float = 16

	@dataclass(slots=True)
	class StrokeObject:
		vertices: list[vec2] = field(default_factory=list)
		color: Color = Black
		width: float = 16

		# contract interface
		def render(self, canvas: pygame.Surface, scale: float):
			Engine.strokeDrawSingle_impl(canvas, scale, self)
			
	strokeData: list[StrokeObject] = field(default_factory=list)

	# public interface
	def strokeCreate(self, initPos: vec2, config: StrokeConfig):
		self.objectSequence.append(self.ObjectIndex(0, len(self.strokeData)))
		self.strokeData.append(self.StrokeObject(vertices=[initPos], color=config.color, width=config.width))
		pygame.draw.circle(self.canvasCache.canvas, config.color,
			Engine.scalePos_impl(initPos, self.canvasCache.scale), (config.width / 2 * self.canvasCache.scale))

	def strokeAppend(self, pos: vec2):
		self.strokeData[-1].vertices.append(pos)
		Engine.strokeDrawSingleAppend_impl(
			self.canvasCache.canvas, self.canvasCache.scale,
			self.strokeData[-1].vertices[-2], pos,
			self.strokeData[-1].color, self.strokeData[-1].width
		)

	# rendering
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

	# ---------------- Rectangle ----------------

	@dataclass(slots=True)
	class RectConfig:
		color: Color = Black
		hollow: bool = False
		hollowWidth: float = 0.0

	@dataclass(slots=True)
	class RectObject:
		pos: vec2 = field(default_factory=vec2)
		dim: vec2 = field(default_factory=vec2)
		conf: Engine.RectConfig | None = None

		def render(self, canvas: pygame.Surface, scale: float):
			Engine.rectDrawSingle_impl(canvas, scale, self)

	rectData: list[RectObject] = field(default_factory=list)

	@staticmethod
	def findRect(pa: vec2, pb: vec2):
		topLeft = vec2(min(pa.x, pb.x), min(pa.y, pb.y))
		bottomRight = vec2(max(pa.x, pb.x), max(pa.y, pb.y))
		return (topLeft, bottomRight - topLeft)
				
	# public interface
	def rectCreate(self, pa: vec2, config: RectConfig):
		self.objectSequence.append(self.ObjectIndex(1, len(self.rectData)))
		self.rectData.append(self.RectObject(pos=pa, conf=replace(config)))
		self.viewProvider = self.rectPreview
	def rectFinish(self, pb: vec2):
		pos, dim = self.findRect(self.rectData[-1].pos, pb)
		self.rectData[-1].pos = pos
		self.rectData[-1].dim = dim
		self.rectDrawSingle_impl(self.canvasCache.canvas, self.canvasCache.scale, self.rectData[-1])
		self.viewProvider = None
		self.rectPreviewPb = None

	'''
	After rectCreate was called, rectPreviewPb must be set immediately in next
	mouse motion event.1
	'''
	rectPreviewPb: vec2 | None = None
	def rectPreview(self) -> pygame.Surface:
		if (self.rectPreviewPb is None): return self.canvasCache.canvas
		preview = self.canvasCache.canvas.copy()
		pos, dim = self.findRect(self.rectData[-1].pos, self.rectPreviewPb)
		Engine.rectDrawSingle_impl(preview, self.canvasCache.scale,
		                           self.RectObject(pos, dim, self.rectData[-1].conf))
		return preview

	# rendering
	@staticmethod
	def rectDrawSingle_impl(canvas: pygame.Surface, scale: float, object: RectObject):
		pygame.draw.rect(canvas, object.conf.color,
						 Engine.scalePos_impl(object.pos, scale) +
						 Engine.scalePos_impl(object.dim, scale),
		                 width=Engine.scaleDist_impl(object.conf.hollowWidth, scale) if object.conf.hollow else 0)

	# ================ Master Rendering ================

	def render_impl(self, canvas: pygame.Surface, scale: float):
		canvas.fill(White)
		#canvas.blit(pygame.transform.scale(pygame.image.load("/home/TX_Jerry/chen.bmp").convert(), canvas.get_size()))
		if (self.circle is not None):
			pygame.draw.circle(canvas, White, (self.circle * scale).toTuple(), 64 * self.canvasCache.scale)
		
		# actual rendering
		# ---------------- Sequencial Rendering ----------------

		for object in self.objectSequence:
			self.bufferList[object.typeIndex][object.index].render(canvas, scale)