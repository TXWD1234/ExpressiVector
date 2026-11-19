# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .widget_infrastructure import *
from .engine_handler import *

@dataclass(slots=True)
class CanvasWidget(RectWidgetBase):
	# ================ Camera System ================

	@dataclass(slots=True)
	class CameraConfig:
		# velocity is in canvas vpc;
		# must be scaled before applying to pos, for uniformed velocity for all scale
		velocity: float = 16
		# zooming factor for zooming out; zoom in is just 1 / zoomFactor
		# applied to the scale state when zooming is performed
		zoomFactor: float = 0.9

	cameraConfig: CameraConfig = field(default_factory=CameraConfig)

	@dataclass(slots=True)
	class CameraState:
		# pos is always the absolute position in the canvas (canvas vpc)
		# representing the top left of the viewport
		pos: vec2 = field(default_factory=lambda: vec2(0.0, 0.0))
		# scale is the factor of the final viewport size; multiplied individually
		# against the w/h of the viewport dimension
		# if scale is smaller then 1.0 (up scaling), to maintain perfect geometry,
		# the engine must redraw
		scale: float = 1.0
		# viewport dimension is determinded by the dimension of the widget
	cameraState: CameraState = field(default_factory=CameraState)

	def findVPPos_impl(self, pos: vec2):
		return pos / self.cameraState.scale + self.cameraState.pos

	def findVPPosFromHanlder_impl(self, pos: tuple[int, int]) -> vec2:
		return self.findVPPos_impl(vec2.fromIvec2(ivec2.fromTuple(pos) - self.pos))

	# @param anchor the point fixed in viewport space before and after zooming;
	#               in vpc
	def zoom_impl(self, newScale: float, anchor: vec2):
		newScale = min(newScale, 16.0)
		self.cameraState.pos = anchor - (anchor - self.cameraState.pos) * (self.cameraState.scale / newScale)
		self.cameraState.scale = newScale

	# ================ Contract Interface ================

	def __post_init__(self):
		# bind to current engine (document)
		# self.cameraState.pos = self.uniform.engine.canvasState.dim * 0.5
		self.uniform.engine.redraw(1.0)
		self.handler = EngineHandler(uniform=self.uniform)

	def draw(self, screen: pygame.Surface):
		super().draw(screen)
		
		# update cache
		if (self.uniform.engine.canvasCache.scale != self.cameraState.scale):
			# cache invalidation; full redraw required
			self.uniform.engine.redraw(self.cameraState.scale)

		# cache validated; draw from cache
		viewportPos: ivec2 = toIvec2(self.cameraState.pos * self.cameraState.scale) # topLeft
		viewportDim: ivec2 = toIvec2(vec2(self.dim.x, self.dim.y))
		screen.blit(self.uniform.engine.view(), self.pos.toTuple(), makeRect(viewportPos, viewportDim))

		self.diff = False

	handler: EngineHandler | None = field(init=False, default=None)

	def handleEvent(self, event):
		match (event.type):
			case Events.MouseEnter:
				self.state.hover = True
				self.diff = True
			case Events.MouseLeave:
				self.state.hover = False
				self.diff = True
			case pygame.MOUSEBUTTONDOWN:
				match (event.button): # State init
					case 1:  # Left Click
						if (self.uniform.editStateTag[-1] == EditStateTag.Nothing): return False
						self.diff = True
						self.uniform.engineState.append(EngineState.Edit)
						self.handler.handleMouseDown(self.findVPPosFromHanlder_impl(event.pos))
					case 2:  # Middle Click
						self.uniform.engineState.append(EngineState.Drag)
					case 3:  # Right Click
						pass
					case 4:  # Scroll Up
						self.zoom_impl(self.cameraState.scale / self.cameraConfig.zoomFactor,
									   self.findVPPosFromHanlder_impl(event.pos))
						self.diff = True
					case 5:  # Scroll Down
						self.zoom_impl(self.cameraState.scale * self.cameraConfig.zoomFactor,
						               self.findVPPosFromHanlder_impl(event.pos))
						self.diff = True
			case pygame.MOUSEBUTTONUP: # State uninit
				match (event.button):
					case 1:  # Left Click
						self.handler.handleMouseUp(self.findVPPosFromHanlder_impl(event.pos))
					case 2:  # Middle Click
						if (self.uniform.engineState[-1] == EngineState.Drag): self.uniform.engineState.pop()
					case 3:  # Right Click
						pass
			case pygame.MOUSEMOTION: # State perform
				match (self.uniform.engineState[-1]):
					case EngineState.Normal:
						#print("normal")
						pass
					case EngineState.Drag:
						#print("drag")
						diff: vec2 = vec2.fromTuple(event.rel) / self.cameraState.scale
						self.cameraState.pos -= diff
						self.diff = True
					case EngineState.Edit:
						#print("edit")
						self.handler.handleMouseMotion(self.findVPPosFromHanlder_impl(event.pos))
						self.diff = True
								
	def update(self):
		super().update()

	# ================ Public Interface ================

	def clear(self):
		self.cameraState.pos = vec2(0.0, 0.0)
		self.cameraState.scale = 1.0
		self.uniform.engine.clear()