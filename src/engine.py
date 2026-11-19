# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .geometry import *
from .rgb import *
from .infrastructure import *
import pygame
from dataclasses import dataclass, field, replace
from typing import Callable, BinaryIO
import struct
import array

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
		self.bufferList.clear()
		self.bufferList.append(self.strokeData)
		self.bufferList.append(self.rectData)

	@dataclass(slots=True)
	class ObjectIndex:
		typeIndex: int = 0
		index: int = 0

		def serialize(self, buf: list[int]):
			buf.append(self.typeIndex)
			buf.append(self.index)
		@staticmethod
		def load(bufIndex: Ptr[int], buf: array.array):
			res = Engine.ObjectIndex(buf[bufIndex.v], buf[bufIndex.v + 1])
			bufIndex.v += 2
			return res

	objectSequence: list[ObjectIndex] = field(default_factory=list)

	def objectSequenceSerialize(self) -> list[int]:
		res = []
		for i in self.objectSequence: i.serialize(res)
		return res

	def objectSequenceWrite(self, f: BinaryIO):
		Engine.writeIntBuffer_impl(f, self.objectSequenceSerialize(), len(self.objectSequence))

	def objectSequenceLoad(self, buf: array.array, size: int):
		index = Ptr[int](v=0)
		self.objectSequence = [Engine.ObjectIndex.load(index, buf) for _ in range(size)]

	def objectSequenceRead(self, f: BinaryIO):
		buf, size = Engine.readIntBuffer_impl(f)
		self.objectSequenceLoad(buf, size)

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

		def serialize(self, buf: list[float], ibuf: list[int]):
			Engine.serializeVec2List_impl(buf, ibuf, self.vertices)
			Engine.serializeColor_impl(buf, self.color)
			Engine.serializeFloat_impl(buf, self.width)
		@staticmethod
		def load(bufIndex: Ptr[int], ibufIndex: Ptr[int],
				 buf: array.array, ibuf: array.array):
			return Engine.StrokeObject(
				Engine.loadVec2List_impl(bufIndex, ibufIndex, buf, ibuf),
				Engine.loadColor_impl(bufIndex, buf),
				Engine.loadFloat_impl(bufIndex, buf))

	strokeData: list[StrokeObject] = field(default_factory=list)

	# save/open
	def strokeSerialize(self) -> tuple[list[float], list[int]]:
		res = []
		ires = []
		for i in self.strokeData: i.serialize(res, ires)
		return (res, ires)

	def strokeWrite(self, f: BinaryIO):
		buf, ibuf = self.strokeSerialize()
		Engine.writeFloatBufferList_impl(f, buf, ibuf, len(self.strokeData))

	def strokeLoad(self, buf: array.array, ibuf: array.array, size: int):
		index = Ptr[int](v=0)
		iindex = Ptr[int](v=0)
		self.strokeData = [Engine.StrokeObject.load(index, iindex, buf, ibuf) for _ in range(size)]

	def strokeRead(self, f: BinaryIO):
		buf, ibuf, size = Engine.readFloatBufferList_impl(f)
		self.strokeLoad(buf, ibuf, size)

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

		def serialize(self, buf: list[float]):
			Engine.serializeColor_impl(buf, self.color)
			Engine.serializeFloat_impl(buf, self.hollowWidth if self.hollow else 0.0)
		@staticmethod
		def load(bufIndex: Ptr[int], buf: array.array):
			return Engine.RectConfig(
				color=Engine.loadColor_impl(bufIndex, buf),
				hollowWidth=(width := Engine.loadFloat_impl(bufIndex, buf)),
				hollow=(width != 0.0))

	@dataclass(slots=True)
	class RectObject:
		pos: vec2 = field(default_factory=vec2)
		dim: vec2 = field(default_factory=vec2)
		conf: Engine.RectConfig | None = None

		def render(self, canvas: pygame.Surface, scale: float):
			Engine.rectDrawSingle_impl(canvas, scale, self)

		def serialize(self, buf: list[float]):
			Engine.serializeVec2_impl(buf, self.pos)
			Engine.serializeVec2_impl(buf, self.dim)
			self.conf.serialize(buf)
		@staticmethod
		def load(bufIndex: Ptr[int], buf: array.array):
			return Engine.RectObject(
				Engine.loadVec2_impl(bufIndex, buf),
				Engine.loadVec2_impl(bufIndex, buf),
				Engine.RectConfig.load(bufIndex, buf))

	rectData: list[RectObject] = field(default_factory=list)

	# save/open
	def rectSerialize(self) -> list[float]:
		res = []
		for i in self.rectData: i.serialize(res)
		return res

	def rectWrite(self, f: BinaryIO):
		Engine.writeFloatBuffer_impl(f, self.rectSerialize(), len(self.rectData))

	def rectLoad(self, buf: array.array, size: int):
		index = Ptr[int](v=0)
		self.rectData = [Engine.RectObject.load(index, buf) for _ in range(size)]

	def rectRead(self, f: BinaryIO):
		buf, size = Engine.readFloatBuffer_impl(f)
		self.rectLoad(buf, size)

	@staticmethod
	def rectFindRect_impl(pa: vec2, pb: vec2):
		topLeft = vec2(min(pa.x, pb.x), min(pa.y, pb.y))
		bottomRight = vec2(max(pa.x, pb.x), max(pa.y, pb.y))
		return (topLeft, bottomRight - topLeft)

	# public interface
	def rectCreate(self, pa: vec2, config: RectConfig):
		self.objectSequence.append(self.ObjectIndex(1, len(self.rectData)))
		self.rectData.append(self.RectObject(pos=pa, conf=replace(config)))
		self.viewProvider = self.rectPreview
	def rectFinish(self, pb: vec2):
		pos, dim = self.rectFindRect_impl(self.rectData[-1].pos, pb)
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
		pos, dim = self.rectFindRect_impl(self.rectData[-1].pos, self.rectPreviewPb)
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

	# ================ Binary Serialization Utility ================
	'''
	Binary Serialization serves for the save/open feature of the project.
	It handles the soft formatting part of the pipeline, converting buffers
	of primitives into engine data.
	The terminology of Binary Serialization is: serialize/load.
	'''

	# ---------------- Serialize ----------------

	@staticmethod
	def serializeFloat_impl(buf: list[float], v: float):
		buf.append(v)

	@staticmethod
	def serializeVec2_impl(buf: list[float], v: vec2):
		buf.append(v.x)
		buf.append(v.y)

	@staticmethod
	def serializeColor_impl(buf: list[float], color: Color):
		c = pygame.Color(color)
		buf.append(float(c.r))
		buf.append(float(c.g))
		buf.append(float(c.b))
		buf.append(float(c.a))

	'''
	All lists serialization based on fbuffer must have an index header
	somewhere else.
	'''

	@staticmethod
	def serializeFloatList_impl(buf: list[float], ibuf: list[int], flist: list[float]):
		ibuf.append(len(flist))
		buf.extend(flist)

	@staticmethod
	def serializeVec2List_impl(buf: list[float], ibuf: list[int], vlist: list[vec2]):
		ibuf.append(len(vlist) * 2)
		buf.extend(f for v in vlist for f in (v.x, v.y))

	# ---------------- Load ----------------

	@staticmethod
	def loadFloat_impl(bufIndex: Ptr[int], buf: array.array) -> float:
		res = buf[bufIndex.v]
		bufIndex.v += 1
		return res

	@staticmethod
	def loadVec2_impl(bufIndex: Ptr[int], buf: array.array) -> vec2:
		res = vec2(buf[bufIndex.v], buf[bufIndex.v + 1])
		bufIndex.v += 2
		return res
	
	@staticmethod
	def loadColor_impl(bufIndex: Ptr[int], buf: array.array) -> Color:
		res = (int(buf[bufIndex.v]), int(buf[bufIndex.v + 1]),
		       int(buf[bufIndex.v + 2]), int(buf[bufIndex.v + 3]))
		bufIndex.v += 4
		return res

	@staticmethod
	def loadFloatList_impl(
		bufIndex: Ptr[int], ibufIndex: Ptr[int],
		buf: array.array, ibuf: array.array) -> list[vec2]:
		size = ibuf[ibufIndex.v]
		ibufIndex.v += 1

		res = [buf[i] for i in range(bufIndex.v, bufIndex.v + size)]

		bufIndex.v += size
		return res

	@staticmethod
	def loadVec2List_impl(
		bufIndex: Ptr[int], ibufIndex: Ptr[int],
		buf: array.array, ibuf: array.array) -> list[vec2]:
		size = ibuf[ibufIndex.v]
		ibufIndex.v += 1

		res = [vec2(buf[i], buf[i + 1]) for i in range(bufIndex.v, bufIndex.v + size, 2)]

		bufIndex.v += size
		return res

	# ================ File IO ================
	'''
	File IO serves for the save/open feature of the project.
	It handles the firm file read/write part of the pipeline, operating on file
	handle and forward the data to Binary Serialization.
	The terminology of Binary Serialization is: write/read.
	'''
	
	# ---------------- Write ----------------
	'''
	All sizes are element size, meaning the count of engine objects, distinguish
	from byte count or primitive count.
	'''

	@staticmethod
	def writeFloatBuffer_impl(f: BinaryIO, buf: list[float], size: int):
		f.write(struct.pack("<2I", size, len(buf)))
		if (size > 0): array.array("f", buf).tofile(f)

	@staticmethod
	def writeIntBuffer_impl(f: BinaryIO, buf: list[int], size: int):
		f.write(struct.pack("<2I", size, len(buf)))
		if (size > 0): array.array("i", buf).tofile(f)

	@staticmethod
	def writeFloatBufferList_impl(f: BinaryIO, buf: list, ibuf: list[int], size: int):
		f.write(struct.pack("<3I", size, len(buf), len(ibuf)))
		if (size > 0):
			array.array("f", buf).tofile(f)
			array.array("i", ibuf).tofile(f)

	def writeDocHeader_impl(self, f: BinaryIO):
		# format identifier
		f.write(b"EVDOC")
		# document dimension
		f.write(struct.pack("<2f", self.canvasState.dim.x, self.canvasState.dim.y))

	def write_impl(self, f: BinaryIO):
		self.writeDocHeader_impl(f)
		self.objectSequenceWrite(f)
		self.strokeWrite(f)
		self.rectWrite(f)

	# ---------------- Read ----------------

	@staticmethod
	def readFloatBuffer_impl(f: BinaryIO) -> tuple[array.array, int]:
		elemSize, bufSize = struct.unpack("<2I", f.read(8))
		buf = array.array("f")
		buf.fromfile(f, bufSize)
		return buf, elemSize

	@staticmethod
	def readIntBuffer_impl(f: BinaryIO) -> tuple[array.array, int]:
		elemSize, bufSize = struct.unpack("<2I", f.read(8))
		buf = array.array("i")
		buf.fromfile(f, bufSize)
		return buf, elemSize

	@staticmethod
	def readFloatBufferList_impl(f: BinaryIO) -> tuple[array.array, array.array, int]:
		elemSize, bufSize, ibufSize = struct.unpack("<3I", f.read(12))
		buf = array.array("f")
		ibuf = array.array("i")
		buf.fromfile(f, bufSize)
		ibuf.fromfile(f, ibufSize)
		return buf, ibuf, elemSize

	def readDocHeader_impl(self, f: BinaryIO) -> bool:
		if (f.read(5) != b"EVDOC"): return False
		self.canvasState.dim = vec2.fromTuple(struct.unpack("<2f", f.read(8)))
		return True

	def read_impl(self, f: BinaryIO):
		if (not self.readDocHeader_impl(f)): return
		self.objectSequenceRead(f)
		self.strokeRead(f)
		self.rectRead(f)

		self.initBufferList()
		self.redraw()