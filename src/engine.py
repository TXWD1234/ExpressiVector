# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .geometry import *
from .rgb import *
from .infrastructure import *
import pygame
from dataclasses import dataclass, field, replace
from collections import OrderedDict
from typing import Callable, BinaryIO, Self
import struct
import array
import io

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

	previewPoint: vec2 | None = None
	'''
	After *Create was called, previewPoint must be set immediately in next
	mouse motion event.
	'''
	

	def view(self) -> pygame.Surface:
		if (self.viewProvider is not None): return self.viewProvider()
		return self.canvasCache.canvas

	def clear(self):
		self.objectSequence.clear()
		for buffer in self.bufferList:
			buffer.clear()
		self.redraw(1.0)

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
		self.bufferList.append(self.stampData)

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
		colorOverride: Color | None = None
		width: float = 16

		def getColor(self): return self.color if self.colorOverride is None else self.colorOverride

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
		color = config.getColor()
		self.objectSequence.append(self.ObjectIndex(0, len(self.strokeData)))
		self.strokeData.append(self.StrokeObject(vertices=[initPos], color=color, width=config.width))
		pygame.draw.circle(self.canvasCache.canvas, color,
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
		colorOverride: Color | None = None
		hollow: bool = False
		hollowWidth: float = 0.0

		def getColor(self): return self.color if self.colorOverride is None else self.colorOverride

		def serialize(self, buf: list[float]):
			Engine.serializeColor_impl(buf, self.getColor())
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
		self.previewPoint = None

	def rectPreview(self) -> pygame.Surface:
		if (self.previewPoint is None): return self.canvasCache.canvas
		preview = self.canvasCache.canvas.copy()
		pos, dim = self.rectFindRect_impl(self.rectData[-1].pos, self.previewPoint)
		Engine.rectDrawSingle_impl(preview, self.canvasCache.scale,
		                           self.RectObject(pos, dim, self.rectData[-1].conf))
		return preview

	# rendering
	@staticmethod
	def rectDrawSingle_impl(canvas: pygame.Surface, scale: float, object: RectObject):
		pygame.draw.rect(canvas, object.conf.getColor(),
						 Engine.scalePos_impl(object.pos, scale) +
						 Engine.scalePos_impl(object.dim, scale),
		                 width=Engine.scaleDist_impl(object.conf.hollowWidth, scale) if object.conf.hollow else 0)

	# ---------------- Bitmap Stamp ----------------

	@dataclass(slots=True)
	class StampConfig:
		textureId: int = -1
		scale: float = 1.0

		def serialize(self, ibuf: list[int], fbuf: list[float]):
			ibuf.append(self.textureId)
			fbuf.append(self.scale)
		@staticmethod
		def load(ibufIndex: Ptr[int], ibuf: array.array,
		         fbufIndex: Ptr[int], fbuf: array.array):
			return Engine.StampConfig(
				Engine.loadInt_impl(ibufIndex, ibuf),
				Engine.loadFloat_impl(fbufIndex, fbuf))

	@dataclass(slots=True)
	class StampObject:
		pos: vec2 = field(default_factory=lambda: vec2(0.0, 0.0))
		conf: Engine.StampConfig | None = None
		engine: Engine | None = None

		def render(self, canvas: pygame.Surface, scale: float):
			self.engine.stampDrawSingle_impl(canvas, scale, self)

		def serialize(self, ibuf: list[int], fbuf: list[float]):
			Engine.serializeVec2_impl(fbuf, self.pos)
			self.conf.serialize(ibuf, fbuf)
		@staticmethod
		def load(ibufIndex: Ptr[int], ibuf: array.array,
		         fbufIndex: Ptr[int], fbuf: array.array):
			return Engine.StampObject(
				pos=Engine.loadVec2_impl(fbufIndex, fbuf),
				conf=Engine.StampConfig.load(ibufIndex, ibuf, fbufIndex, fbuf))

	stampData: list[StampObject] = field(default_factory=list)
	stampTextureData: list[pygame.Surface] = field(default_factory=list)

	@staticmethod
	def stampWriteTexture_impl(f: BinaryIO, texture: pygame.Surface):
		buf = io.BytesIO()
		pygame.image.save(texture, buf, ".png")
		data = buf.getvalue()
		f.write(struct.pack("<I", len(data)))
		f.write(data)
	def stampWriteTextureData_impl(self, f: BinaryIO):
		f.write(struct.pack("<I", len(self.stampTextureData)))
		for texture in self.stampTextureData:
			self.stampWriteTexture_impl(f, texture)

	@staticmethod
	def stampReadTexture_impl(f: BinaryIO) -> pygame.Surface:
		size, = struct.unpack("<I", f.read(4))
		return pygame.image.load(io.BytesIO(f.read(size)), ".png").convert_alpha()
	def stampReadTextureData_impl(self, f: BinaryIO):
		count, = struct.unpack("<I", f.read(4))
		self.stampTextureData = [self.stampReadTexture_impl(f) for i in range(count)]

	def stampSerialize(self) -> tuple[list[int], list[float]]:
		ibuf = []
		fbuf = []
		for i in self.stampData: i.serialize(ibuf, fbuf)
		return (ibuf, fbuf)

	def stampWrite(self, f: BinaryIO):
		self.stampWriteTextureData_impl(f)
		#Engine.write




	stampTextureCache: OrderedDict[tuple[int, int, int], pygame.Surface] = field(default_factory=OrderedDict)

	# @param scale combined
	# lazy loading cache
	# key: (textureId, w, h)
	def stampAcquireTexture(self, textureId: int, scale: float) -> pygame.Surface:
		key = self.stampTextureCacheFindKey_impl(textureId, scale)

		if (key in self.stampTextureCache): # in cache
			self.stampTextureCache.move_to_end(key)
			return self.stampTextureCache[key]

		texture = pygame.transform.smoothscale(
			self.stampTextureData[key[0]], (key[1], key[2]))
		self.stampTextureCache[key] = texture
		# cache size cap
		if (len(self.stampTextureCache) > 64):
			self.stampTextureCache.popitem(last=False)
		return texture
	# @param scale combined scale
	def stampTextureCacheFindKey_impl(self, textureId: int, scale: float):
		src = self.stampTextureData[textureId]
		w = max(1, int(src.get_width () * scale))
		h = max(1, int(src.get_height() * scale))
		return (textureId, w, h)
	# @param scale global scale
	def stampTextureCacheFindKey(self, obj: StampObject, scale: float):
		return self.stampTextureCacheFindKey_impl(obj.conf.textureId, obj.conf.scale * scale)

	# public interface
	def stampCreate(self, pos: vec2, config: StampConfig):
		self.objectSequence.append(Engine.ObjectIndex(2, len(self.stampData)))
		self.stampData.append(Engine.StampObject(pos=pos, conf=replace(config), engine=self))
		self.stampDrawSingle_impl(self.canvasCache.canvas, self.canvasCache.scale, self.stampData[-1])

	stampPreviewConfig: StampConfig | None = None
	def stampSetPreview(self, config: StampConfig):
		self.stampPreviewConfig = config
		self.viewProvider = self.stampPreview
	def stampStopPreview(self):
		self.viewProvider = None


	def stampPreview(self) -> pygame.Surface:
		if (self.previewPoint is None): return self.canvasCache.canvas
		preview = self.canvasCache.canvas.copy()
		self.stampDrawSingle_impl(preview, self.canvasCache.scale,
		                          Engine.StampObject(self.previewPoint, self.stampPreviewConfig))
		return preview

	def stampDrawSingle_impl(self, canvas: pygame.Surface, scale: float, obj: StampObject):
		texture = self.stampAcquireTexture(obj.conf.textureId, obj.conf.scale * scale)
		pos = Engine.scalePos_impl(obj.pos, scale)
		canvas.blit(texture, (pos[0] - texture.get_width() // 2, pos[1] - texture.get_height() // 2))

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

	@dataclass(slots=True)
	class OutBinary:
		fbuf: list[float] = field(default_factory=list)
		ibuf: list[int] = field(default_factory=list)
	outBinary: OutBinary | None = None

	@dataclass(slots=True)
	class InBinary:
		fbuf: array.array = field(default_factory=lambda: array.array("f"))
		ibuf: array.array = field(default_factory=lambda: array.array("i"))
		findex: int = 0
		iindex: int = 0
	inBinary: InBinary | None = None

	# ---------------- Serialize ----------------

	def serializeFloat_impl(self, v: float):
		self.outBinary.fbuf.append(v)
	def serializeInt_impl(self, v: int):
		self.outBinary.ibuf.append(v)

	def serializeVec2_impl(self, v: vec2):
		self.serializeFloat_impl(v.x)
		self.serializeFloat_impl(v.y)

	def serializeColor_impl(self, color: Color):
		c = pygame.Color(color)
		self.serializeInt_impl(c.r)
		self.serializeInt_impl(c.g)
		self.serializeInt_impl(c.b)
		self.serializeInt_impl(c.a)

	'''
	All lists serialization based on fbuffer must have an index header
	somewhere else.
	'''

	def serializeFloatList_impl(self, flist: list[float]):
		self.serializeInt_impl(len(flist))
		self.outBinary.fbuf.extend(flist)
	def serializeIntList_impl(self, ilist: list[int]):
		self.serializeInt_impl(len(ilist))
		self.outBinary.ibuf.extend(ilist)

	def serializeVec2List_impl(self, vlist: list[vec2]):
		self.serializeInt_impl(len(vlist) * 2)
		self.outBinary.fbuf.extend(f for v in vlist for f in (v.x, v.y))
		
	# ---------------- Load ----------------

	def loadFloat_impl(self) -> float:
		val = self.inBinary.fbuf[self.inBinary.findex]
		self.inBinary.findex += 1
		return val
	def loadInt_impl(self) -> int:
		val = self.inBinary.ibuf[self.inBinary.iindex]
		self.inBinary.iindex += 1
		return val

	def loadVec2_impl(self) -> vec2:
		return vec2(self.loadFloat_impl(), self.loadFloat_impl())
	
	def loadColor_impl(self) -> Color:
		return (
			self.loadInt_impl(),
			self.loadInt_impl(),
			self.loadInt_impl(),
			self.loadInt_impl())

	def loadFloatList_impl(self) -> list[float]:
		size = self.loadInt_impl()
		val =  [self.inBinary.fbuf[self.inBinary.findex + i] for i in range(0, size)]
		self.inBinary.findex += size
		return val

	def loadVec2List_impl(self) -> list[vec2]:
		size = self.loadInt_impl()
		val =  [vec2(self.inBinary.fbuf[self.inBinary.findex + i],
		             self.inBinary.fbuf[self.inBinary.findex + i + 1]) for i in range(0, size, 2)]
		self.inBinary.findex += size
		return val

	# ================ File IO ================
	'''
	File IO serves for the save/open feature of the project.
	It handles the firm file read/write part of the pipeline, operating on file
	handle and forward the data to Binary Serialization.
	The terminology of Binary Serialization is: write/read.
	'''
		
	def writeDocHeader_impl(self, f: BinaryIO):
		# format identifier
		f.write(b"EVDOC")
		# document dimension
		f.write(struct.pack("<2f", self.canvasState.dim.x, self.canvasState.dim.y))

	def writeBinary_impl(self, f: BinaryIO):
		f.write(struct.pack("<2I", len(self.outBinary.fbuf), len(self.outBinary.ibuf)))

		if (len(self.outBinary.fbuf) > 0): array.array("f", self.outBinary.fbuf).tofile(f)
		if (len(self.outBinary.ibuf) > 0): array.array("i", self.outBinary.ibuf).tofile(f)

	def write_impl(self, f: BinaryIO):
		# serialize
		

		self.writeDocHeader_impl(f)
		self.writeBinary_impl(f)
		self.stampWriteTextureData_impl(f)

	def write(self, path: Path):
		self.outBinary = Engine.OutBinary()
		with open(path, "wb") as f:
			self.write_impl(f)
		self.outBinary = None

	# ---------------- Read ----------------

	def readBinary_impl(self, f: BinaryIO):
		fsize, isize = struct.unpack("<2I", f.read(8))
		self.inBinary = Engine.InBinary()
		self.inBinary.fbuf.fromfile(f, fsize)
		self.inBinary.ibuf.fromfile(f, isize)

	def readDocHeader_impl(self, f: BinaryIO) -> bool:
		if (f.read(5) != b"EVDOC"): return False
		self.canvasState.dim = vec2.fromTuple(struct.unpack("<2f", f.read(8)))
		return True

	def read_impl(self, f: BinaryIO):
		if (not self.readDocHeader_impl(f)): return
		self.readBinary_impl(f)
		self.stampReadTextureData_impl(f)

	def read(self, path: Path):
		with open(path, "rb") as f:
			self.read_impl(f)
		self.initBufferList()
		self.redraw(1.0)
		self.inBinary = None

	# ---------------- Export ----------------

	def export(self, path: Path):
		surface = pygame.Surface((self.canvasState.dim * 1.0).toIvec2().toTuple(), pygame.SRCALPHA)
		self.render_impl(surface, 1.0)
		pygame.image.save(surface, path)