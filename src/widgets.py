# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .widget_infrastructure import *
from .canvas_widget import *

# ============================================================================
# **************** Application Specific Widget Implementation ****************
# ============================================================================
'''
Widgets implemented in this file are application specific widgets. In which
implies deliberate absence of reusability and generalization, as well as
deliberate presence hardcoding custom logic.
'''

# -----------------------------------------
# ················ Sidebar ················
# -----------------------------------------

def setEditStateCb_impl(w: IconedPushButtonWidget, state: EditState):
	w.uniform.editState = state if w.uniform.editState != state else EditState.Nothing
	w.uniform.app.editStateUpdate()

@dataclass(slots=True)
class SidebarWidget(RectWidgetVLayout):

	def addTool_impl(self, icon: str, state: EditState):
		image = pygame.image.load(getProgramDir() / icon).convert_alpha()
		with pygame.PixelArray(image) as pixels:
			pixels.replace((0, 0, 0), (255, 255, 255), 0.1)
		self.addWidget(
			LinearLayoutAttribute(absolute=True),
		    IconedPushButtonWidget,
			source=image,
			onPress=lambda w: setEditStateCb_impl(w, state))

	# ================ Contract Interface ================

	def __post_init__(self):
		self.addTool_impl("assets/stroke-tool-icon.png", EditState.Stroke)

	def activateLayout(self):
		proportion: float = self.dim.x / self.dim.y
		for attrib in self.solver.widgetAttribs:
			attrib.proportion = proportion
		return super().activateLayout()

	def draw(self, screen):
		return RectWidgetBase.draw(self, screen)

# --------------------------------------------------
# ················ Configure Widget ················
# --------------------------------------------------
'''
Hierarchy: Widget -> Panel -> Section -> Entry
'''

# ################ Entry ################

@dataclass(slots=True, kw_only=True)
class ConfigHEntryBase[T: RectWidgetBase](RectWidgetHLayout):

	# ================ Contract Interface ================

	text: InitVar[str]
	entryWidgetType: InitVar[type[T]]
	entryWidgetArgs: InitVar[dict]
	proportion: InitVar[tuple[int, int] | None] = None

	entryWidget: T | None = field(init=False, default=None)
	labelWidget: LabelWidget | None = field(init=False, default=None)
	oldWidth: int = 0
	unitHeight: int = 0

	def __post_init__(self, text: str, entryWidgetType: type[T], entryWidgetArgs: dict,
	                  proportion: tuple[int, int] | None = None):
		self.labelWidget = self.addWidget(LinearLayoutAttribute(
			proportion=proportion[0] if proportion is not None else 1), LabelWidget)
		self.labelWidget.overlay.styleSheet.fontSize = int(self.uniform.fontSize * 0.7)
		self.labelWidget.text = text

		self.entryWidget = self.addWidget(
			LinearLayoutAttribute(proportion=proportion[1] if proportion is not None else 1),
			entryWidgetType, **entryWidgetArgs)

	# report the height of this entry in unit
	# will be called after width is determinded
	def reportHeight(self) -> int:
		if (self.oldWidth != self.dim.x):
			self.oldWidth = self.dim.x
			self.unitHeight = self.labelWidget.setText()
		return max(self.unitHeight, self.entryWidget.reportHeight())

	# ================ Public Interface ================

# ################ Section ################

@dataclass(slots=True)
class ConfigSectionContent(RectWidgetUnitedVLayout):
	'''
	Container of Entrys.
	All sub widgets must be entrys.
	'''
	pass

@dataclass(slots=True, kw_only=True)
class ConfigSection(RectWidgetBase):
	content: ConfigSectionContent | None = field(init=False, default=None)
	nameLabel: pygame.Surface | None = field(init=False, default=None)

	# ================ Contract Interface ================

	name: InitVar[str]

	def __post_init__(self, name: str):
		self.content = self.addWidget(ConfigSectionContent)
		self.nameLabel = self.uniform.font.renderSingle_impl(
			name, self.uniform.fontSize, self.styleSheet.fontColor)
		
	def activateLayout(self):
		self.content.dim = self.dim - ivec2(2 * self.uniform.unit, self.nameLabel.get_height() + self.uniform.unit)
		self.content.pos = self.pos + ivec2(self.uniform.unit, self.uniform.unit // 4 + self.nameLabel.get_height())
		return super().activateLayout()

	def reportHeight(self):
		return self.content.reportHeight() + 2

	def draw(self, screen: pygame.Surface):
		'''
		Appearance:
		- Name -------
		|            |
		| Content    |
		|            |
		--------------
		'''
		screen.blit(self.nameLabel, (self.pos.x + self.uniform.unit + self.styleSheet.margin, self.pos.y + self.styleSheet.margin))
		pygame.draw.rect(screen, self.styleSheet.lineColor, makeRect(self.pos.offsetY(self.nameLabel.get_height() // 2 + self.styleSheet.margin).offsetX(self.styleSheet.margin), ivec2(self.styleSheet.lineWidth, self.dim.y - self.styleSheet.margin * 2 - self.nameLabel.get_height() // 2)))
		pygame.draw.rect(screen, self.styleSheet.lineColor, makeRect(self.pos.offsetY(self.nameLabel.get_height() // 2 + self.styleSheet.margin).offsetX(self.dim.x - self.styleSheet.lineWidth - self.styleSheet.margin), ivec2(self.styleSheet.lineWidth, self.dim.y - self.styleSheet.margin * 2 - self.nameLabel.get_height() // 2)))
		pygame.draw.rect(screen, self.styleSheet.lineColor, makeRect(self.pos.offsetY(self.dim.y - self.styleSheet.lineWidth - self.styleSheet.margin).offsetX(self.styleSheet.margin), ivec2(self.dim.x - 2 * self.styleSheet.margin, self.styleSheet.lineWidth)))
		pygame.draw.rect(screen, self.styleSheet.lineColor, makeRect(self.pos.offsetY(self.nameLabel.get_height() // 2 + self.styleSheet.margin).offsetX(self.styleSheet.margin), ivec2(self.uniform.unit - self.styleSheet.lineWidth * 4, self.styleSheet.lineWidth)))
		pygame.draw.rect(screen, self.styleSheet.lineColor, makeRect(self.pos.offsetY(self.nameLabel.get_height() // 2 + self.styleSheet.margin).offsetX(self.uniform.unit + self.nameLabel.get_width() + self.styleSheet.margin + self.styleSheet.lineWidth * 4),
		                                                             ivec2(self.dim.x - (self.uniform.unit + self.nameLabel.get_width()) - self.styleSheet.margin * 2 - self.styleSheet.lineWidth * 4, self.styleSheet.lineWidth)))

		self.content.draw(screen)

		self.diff = False

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(RectWidgetBase.StyleSheet):
		fontColor: Color = DefaultColor
		lineWidth: int = 10
		lineColor: Color = DefaultColor
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

# ################ Panel ################

@dataclass(slots=True)
class ConfigPanel(RectWidgetRigidUnitedVLayout):
	'''
	Container of Sections.
	All sub widgets must be sections. (with exceptions)
	'''

	# ================ Contract Interface ================

	def draw(self, screen: pygame.Surface):
		'''
		Draw within range.
		'''
		prevClip = screen.get_clip()

		# DevNote: Panel Name

		screen.set_clip(makeRect(self.pos, self.dim))
		RectWidgetBase.draw(self, screen)
		super().draw(screen)

		screen.set_clip(prevClip)

	def handleEvent(self, event):
		if (super().handleEvent(event)): return True

		match (event.type):
			case pygame.MOUSEBUTTONDOWN | pygame.MOUSEBUTTONUP:
				match (event.button):
					case 4:  # Scroll Up
						diff: int = self.pos.y - min(w.pos.y for w in self.widgets if w.visible())
						if (diff > 0):
							for w in self.widgets:
								w.move(ivec2(0, min(self.styleSheet.scrollVel, diff)))
								w.subWidgetHandleMouseDisplacement(ivec2.fromTuple(pygame.mouse.get_pos()))
							self.diff = True
					case 5:  # Scroll Down
						diff: int = max(w.pos.y + w.dim.y for w in self.widgets if w.visible()) - (self.pos.y + self.dim.y)
						if (diff > 0):
							for w in self.widgets:
								w.move(ivec2(0, -min(self.styleSheet.scrollVel, diff)))
								w.subWidgetHandleMouseDisplacement(ivec2.fromTuple(pygame.mouse.get_pos()))
							self.diff = True

	@dataclass(slots=True)
	class StyleSheet(RectWidgetUnitedVLayout.StyleSheet):
		scrollVel: int = 10
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class ConfigWidget(RectWidgetBase):
	pass

# ------------------------------------------------
# ················ Custom Widgets ················
# ------------------------------------------------


# ################ Color Picker ################

# rainbow
hueArr = [
	(255, 0,   0  ),
	(255, 255, 0  ),
	(0,   255, 0  ),
	(0,   255, 255),
	(0,   0,   255),
	(255, 0,   255),
	(255, 0,   0  )
]

def normalizeColor(rgb: Color) -> Color:
	return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)

# rgb -> hsv
def findHSV(rgb: Color) -> tuple[Color, float, float]:
	r, g, b = normalizeColor(rgb)
	cmax = max(r, g, b)
	cmin = min(r, g, b)
	delta = cmax - cmin

	v = cmax # value
	s = delta / v if v != 0 else 1.0 # saturation
	# Color = Brightness * (White * (1 - Saturation) + Hue * Saturation)
	h = (int((r - cmin) / delta * 255),
		 int((g - cmin) / delta * 255),
		 int((b - cmin) / delta * 255)) if delta != 0 else (255, 0, 0)
	return (h, s, v)

def findTFromHue(hue: Color):
    r, g, b = normalizeColor(hue)
    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin

    if delta == 0: return 0.0
    if cmax == r: seg = (g - b) / delta
    elif cmax == g: seg = 2.0 + (b - r) / delta
    else: seg = 4.0 + (r - g) / delta
    return (seg % 6.0) / 6.0

@dataclass(slots=True)
class ColorPickerHue(SliderHWidget):
	color: Color = field(default_factory=lambda: (255, 0, 0)) # hue
	texture: pygame.Surface | None = field(init=False, default=None)

	onColorChange: Callable[[], None] | Callable[[Self], None] = lambda: None

	def handleSlide_impl(self):
		# resolve color

		i = int(math.floor(self.value * 6))
		t = self.value * 6 - i

		if (i == 6): self.color = hueArr[6]
		else: self.color = lerpColor(hueArr[i], hueArr[i + 1], t)

		self.dragger.state.colorOverride = self.color
		optionalCall(self.onColorChange, self)

	# ================ Public Interface ================

	def setHue(self, color: Color):
		self.color = color
		self.setValue(findTFromHue(color))
		self.dragger.state.colorOverride = self.color
		optionalCall(self.onColorChange, self)

	# ================ Contract Interface ================

	def __post_init__(self):
		self.onValueChange = self.handleSlide_impl

	def activateLayout(self):
		super().activateLayout()

		if (self.dim.y == 0): return
		
		# create gradient texture
		palette = pygame.Surface((7, 1))
		palette.set_at((0, 0), hueArr[0])
		palette.set_at((1, 0), hueArr[1])
		palette.set_at((2, 0), hueArr[2])
		palette.set_at((3, 0), hueArr[3])
		palette.set_at((4, 0), hueArr[4])
		palette.set_at((5, 0), hueArr[5])
		palette.set_at((6, 0), hueArr[6])

		self.texture = makeRoundedTexture(pygame.transform.smoothscale(
			palette, (self.dim - ivec2(self.styleSheet.margin * 2)).toTuple()),
			self.styleSheet.roundCornerRadius)

		self.dragger.styleSheet.borderWidth = 2
		self.dragger.styleSheet.borderColor = White
		self.dragger.styleSheet.hoverBorderColor = White
		self.dragger.state.colorOverride = Red

	def draw(self, screen: pygame.Surface):
		# gradient drawing
		screen.blit(self.texture, (self.pos + ivec2(self.styleSheet.margin)).toTuple())

		# ordinary drawing
		if (self.styleSheet.borderWidth != 0):
			draw.rect(screen, self.styleSheet.hoverBorderColor if self.state.hover else self.styleSheet.borderColor,
			          makeRect(self.pos + ivec2(self.styleSheet.margin, self.styleSheet.margin),
						       self.dim - ivec2(self.styleSheet.margin * 2, self.styleSheet.margin * 2)),
					  width=self.styleSheet.borderWidth,
					  border_radius=self.styleSheet.roundCornerRadius)
		tryCall(self.overlay, "draw", screen, self)
		self.dragger.draw(screen)
		self.diff = False

	def reportHeight(self): return 1


@dataclass(slots=True)
class ColorPickerSV(RectWidgetBase):
	hue: Color = field(default_factory=lambda: (255, 0, 0)) # hue
	color: Color = field(default_factory=lambda: (255, 0, 0)) # result color

	texture: pygame.Surface | None = field(init=False, default=None)
	dragger: DragWidget | None = field(init=False, default=None)

	onColorChange: Callable[[], None] | Callable[[Self], None] = lambda: None

	# create gradient texture
	def composeTexture_impl(self):
		palette = pygame.Surface((2, 2))
		palette.set_at((0, 0), (255, 255, 255))
		palette.set_at((1, 0), self.hue)
		palette.set_at((0, 1), (0, 0, 0))
		palette.set_at((1, 1), (0, 0, 0))

		self.texture = makeRoundedTexture(pygame.transform.smoothscale(
			palette, (self.dim - ivec2(self.styleSheet.margin * 2)).toTuple()),
			self.styleSheet.roundCornerRadius)

	def composeColor_impl(self):
		xt, yt = self.findDraggerT()
		#print(xt, yt)
		self.color = orderedLerpColor(orderedLerpColor(self.hue, (255, 255, 255), 1 - xt), (0, 0, 0), 1 - yt)
		self.dragger.state.colorOverride = self.color
		optionalCall(self.onColorChange, self)

	def findDraggerT(self) -> tuple[float, float]:
		return ((self.dragger.pos.x - self.pos.x - self.styleSheet.margin + self.styleSheet.draggerRadius) / (self.dim.x - self.styleSheet.margin * 2),
				(self.dragger.pos.y - self.pos.y - self.styleSheet.margin + self.styleSheet.draggerRadius) / (self.dim.y - self.styleSheet.margin * 2))

	def findDraggerPosRangeBegin_impl(self, begin: int) -> tuple[int, int]:
		return begin + self.styleSheet.margin - self.styleSheet.draggerRadius
	def findDraggerPosRangeEnd_impl(self, end: int) -> tuple[int, int]:
		return end - self.styleSheet.margin - self.styleSheet.draggerRadius
	
	def handleDrag_impl(self):
		# constraint dragger pos
		self.dragger.pos.x = clamp(
			self.dragger.pos.x,
			self.findDraggerPosRangeBegin_impl(self.pos.x),
			self.findDraggerPosRangeEnd_impl(self.pos.x + self.dim.x))
		self.dragger.pos.y = clamp(
			self.dragger.pos.y,
			self.findDraggerPosRangeBegin_impl(self.pos.y),
			self.findDraggerPosRangeEnd_impl(self.pos.y + self.dim.y))

		self.composeColor_impl()
		self.diff = True

	# ================ Public Interface ================

	def setHue(self, color: Color):
		self.hue = color
		self.composeTexture_impl()
		self.composeColor_impl()
		self.diff = True

	def setSV(self, s: float, v: float):
		self.color = orderedLerpColor(orderedLerpColor(self.hue, (255, 255, 255), s), (0, 0, 0), 1 - v)
		self.dragger.pos.x = lerp(self.findDraggerPosRangeBegin_impl(self.pos.x),
		                          self.findDraggerPosRangeEnd_impl(self.pos.x + self.dim.x), s)
		self.dragger.pos.y = lerp(self.findDraggerPosRangeBegin_impl(self.pos.y),
								  self.findDraggerPosRangeEnd_impl(self.pos.y + self.dim.y), 1 - v)

	# ================ Contract Interface ================

	def draw(self, screen: pygame.Surface):
		# draw texture
		screen.blit(self.texture, (self.pos + ivec2(self.styleSheet.margin)).toTuple())

		old = screen.get_clip()
		screen.set_clip(makeMarginedRect(self.pos, self.dim, self.styleSheet.margin))
		self.dragger.draw(screen)
		screen.set_clip(old)

	def activateLayout(self):
		if (self.dragger is not None or self.dim.y == 0): return
		self.composeTexture_impl()
		self.dragger = self.addWidget(
			DragWidget, onDrag=self.handleDrag_impl,
			pos=ivec2(self.findDraggerPosRangeEnd_impl(self.pos.x + self.dim.x),
			          self.findDraggerPosRangeBegin_impl(self.pos.y)),
			dim=ivec2(self.styleSheet.draggerRadius * 2))
		self.dragger.styleSheet.roundCornerRadius = self.styleSheet.draggerRadius
		self.dragger.styleSheet.borderWidth = 2
		self.dragger.styleSheet.borderColor = White
		self.dragger.styleSheet.hoverBorderColor = White
		self.dragger.state.colorOverride = Red

	def reportHeight(self): return 7

	def handleEvent(self, event):
		if (super().handleEvent(event)): return True

		if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
			self.dragger.pos = ivec2.fromTuple(event.pos)
			self.dragger.handleEvent(event)
			self.handleDrag_impl()

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet:
		margin: int = 0
		roundCornerRadius: int = 0
		draggerRadius: int = 8
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class ColorPickerSetter(RectWidgetVLayout):
	color: Color = Red

	onColorChange: Callable[[], None] | Callable[[Self], None] = lambda: None

	r: IntegerFieldWidget | None = field(init=False, default=None)
	g: IntegerFieldWidget | None = field(init=False, default=None)
	b: IntegerFieldWidget | None = field(init=False, default=None)

	def handleRChange_impl(self): self.color = (self.r.value , self.color[1], self.color[2]); optionalCall(self.onColorChange, self)
	def handleGChange_impl(self): self.color = (self.color[0], self.g.value , self.color[2]); optionalCall(self.onColorChange, self)
	def handleBChange_impl(self): self.color = (self.color[0], self.color[1], self.b.value ); optionalCall(self.onColorChange, self)

	# ================ Contract Interface ================

	def __post_init__(self):
		self.r = self.addWidget(LinearLayoutAttribute(order=0), ConfigHEntryBase, text="Red"  , entryWidgetType=IntegerFieldWidget, entryWidgetArgs={"onValueChange": self.handleRChange_impl, "scope": (0, 255)}, proportion=(2, 5)).entryWidget
		self.g = self.addWidget(LinearLayoutAttribute(order=1), ConfigHEntryBase, text="Green", entryWidgetType=IntegerFieldWidget, entryWidgetArgs={"onValueChange": self.handleGChange_impl, "scope": (0, 255)}, proportion=(2, 5)).entryWidget
		self.b = self.addWidget(LinearLayoutAttribute(order=2), ConfigHEntryBase, text="Blue" , entryWidgetType=IntegerFieldWidget, entryWidgetArgs={"onValueChange": self.handleBChange_impl, "scope": (0, 255)}, proportion=(2, 5)).entryWidget

	def reportHeight(self): return 3

	# ================ Public Interface ================

	def setColor(self, color: Color):
		self.color = color
		self.r.setValue(color[0])
		self.g.setValue(color[1])
		self.b.setValue(color[2])

@dataclass(slots=True)
class ColorPickerWidgetContent(RectWidgetUnitedVLayout):
	color: Color = Red

	onConfirm: Callable[[], None] | Callable[[Self], None] = lambda: None

	hue:     ColorPickerHue     | None = field(init=False, default=None)
	sv:      ColorPickerSV      | None = field(init=False, default=None)
	setter:  ColorPickerSetter  | None = field(init=False, default=None)
	confirm: ConfirmationWidget | None = field(init=False, default=None)

	duringChangeResolution: bool = False

	def handleHueChange(self):
		if (self.duringChangeResolution): return
		self.duringChangeResolution = True
		self.sv.setHue(self.hue.color); self.color = self.sv.color; self.interfaceSetColor_impl()
		self.duringChangeResolution = False
	def handleSVChange (self):
		if (self.duringChangeResolution): return
		self.duringChangeResolution = True
		self.color = self.sv.color; self.interfaceSetColor_impl()
		self.duringChangeResolution = False
	def handleColorSet (self):
		if (self.duringChangeResolution): return
		self.duringChangeResolution = True
		self.color = self.setter.color; self.pickerSetColor_impl()
		self.duringChangeResolution = False

	def pickerSetColor_impl(self):
		h, s, v = findHSV(self.color)
		self.hue.setHue(h)
		self.sv.setHue(h)
		self.sv.setSV(s, v)

	def interfaceSetColor_impl(self):
		self.setter.setColor(self.color)

	def setColor(self, color: Color):
		self.color = color
		self.pickerSetColor_impl(color)
		self.setter.setColor(color)

	# ================ Contract Interface ================

	def __post_init__(self):
		self.sv      = self.addWidget(UnitedLinearLayoutAttribute(order=0), ColorPickerSV     , onColorChange=self.handleSVChange )
		self.hue     = self.addWidget(UnitedLinearLayoutAttribute(order=1), ColorPickerHue    , onColorChange=self.handleHueChange)
		self.setter  = self.addWidget(UnitedLinearLayoutAttribute(order=2), ColorPickerSetter , onColorChange=self.handleColorSet )
		self.confirm = self.addWidget(UnitedLinearLayoutAttribute(order=3), ConfirmationWidget, onAction     =self.onConfirm      )

	def reportHeight(self):
		return sum(w.reportHeight() for w in self.widgets)

# ################ Presets ################
'''
--- Architecture of the presets ---
Presets are functions that takes a (potentially empty) widget object and modify
it to construct the targeted widget.
Treat them as factory functions, with the only difference being they don't directly
start the lifetime of an object. 
*"Why not a directly construct it?" Because in this unholy fried codebase, widgets
must be constructed by parent.*
'''

# ================ Helpers ================

def sectionAdd(section: ConfigSection, *args, **kwargs):
	return section.content.addWidget(
		UnitedLinearLayoutAttribute(), ConfigHEntryBase,
		*args, **kwargs).entryWidget
	
# ================ General Presets ================

def configSectionColor(section: ConfigSection):
	section.content = section.addWidget(ColorPickerWidgetContent)

# ================ Stroke ================

def configSectionStrokeSize(section: ConfigSection):
	section.content.addWidget(
		UnitedLinearLayoutAttribute(), ColorPickerSV)
	sectionAdd(section, text="Width", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=IntegerFieldWidget, entryWidgetArgs={"scope": (0, 100)}, proportion=(1, 2))
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=SliderHWidget, entryWidgetArgs={})

# ---------------------------------------------
# ················ Application ················
# ---------------------------------------------

@dataclass(slots=True, weakref_slot=True)
class ApplicationWidget(RectWidgetHLayout):
	configWidgets: list[ConfigWidget] = field(default_factory=list)

	canvasWidget: CanvasWidget | None = field(init=False, default=None)
	#configWidget: ConfigWidget | None = field(init=False, default=None)
	configWidget: ConfigPanel | None = field(init=False, default=None)
	sidebarWidget: SidebarWidget | None = field(init=False, default=None)	

	def __post_init__(self):
		self.canvasWidget = self.addWidget(LinearLayoutAttribute(order=0), CanvasWidget)
		self.sidebarWidget = self.addWidget(LinearLayoutAttribute(order=2, absolute=True, proportion=0.04), SidebarWidget)
		
		self.configWidget = self.addWidget(LinearLayoutAttribute(order=1, absolute=True, visible=False, proportion=0.2), ConfigPanel)
		#self.configWidget.addWidget(UnitedLinearLayoutAttribute(), ColorPickerWidgetContent)
		configSectionColor(self.configWidget.addWidget(UnitedLinearLayoutAttribute(), ConfigSection, name="Color"))		

	# Contrainted Contract Interface
	# Will be called everytime with updated uniform state
	def editStateUpdate(self):
		if (self.uniform.editState == EditState.Nothing):
			self.configWidget.hide()
		else:
			self.configWidget.show()
			self.configWidget.widgets[0].activateLayout()



theme: WidgetTheme = {

	RectWidgetBase: RectWidgetBase.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	RectWidgetHLayout: RectWidgetHLayout.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	RectWidgetVLayout: RectWidgetVLayout.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	PushButtonWidget: PushButtonWidget.StyleSheet(
		backgroundColor=Blue, roundCornerRadius=20, margin=0, pressColor=(0x8e, 0x8e, 0x8f)),
	IconedPushButtonWidget: IconedPushButtonWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
		roundCornerRadius=10, margin=10, iconMargin=5),
	LabeledPushButtonWidget: LabeledPushButtonWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
		roundCornerRadius=10, margin=10, textMargin=5),
	ToggleWidget: ToggleWidget.StyleSheet(
		onColor=Blue, offColor=LightGray, nodeColor=White, nodePadding=4),
	DragWidget: DragWidget.StyleSheet(
		backgroundColor=Blue, roundCornerRadius=20, margin=0),
	SliderHWidget: SliderWidgetBase.StyleSheet(
		backgroundColor=(0xae, 0xae, 0xaf), backgroundEmptyColor=(0x55, 0x56, 0x56), hoverColor=(0xce, 0xce, 0xcf),
		draggerNormalColor=(0x7e, 0x7e, 0x7f), draggerHoverColor=(0x5e, 0x5e, 0x5f), draggerDragColor=(0x3f, 0x3f, 0x3f),
		draggerMargin=-5, roundCornerRadius=20, margin=10),
	SliderVWidget: SliderWidgetBase.StyleSheet(
		backgroundColor=(0xae, 0xae, 0xaf), backgroundEmptyColor=(0x55, 0x56, 0x56), hoverColor=(0xce, 0xce, 0xcf),
		draggerNormalColor=(0x7e, 0x7e, 0x7f), draggerHoverColor=(0x5e, 0x5e, 0x5f), draggerDragColor=(0x3f, 0x3f, 0x3f),
		draggerMargin=5, roundCornerRadius=20, margin=10),
	IntegerSliderHWidget: IntegerSliderWidgetBase.StyleSheet(
		backgroundColor=(0xae, 0xae, 0xaf), backgroundEmptyColor=(0x55, 0x56, 0x56), hoverColor=(0xce, 0xce, 0xcf),
		draggerNormalColor=(0x7e, 0x7e, 0x7f), draggerHoverColor=(0x5e, 0x5e, 0x5f), draggerDragColor=(0x3f, 0x3f, 0x3f),
		draggerMargin=-5, roundCornerRadius=20, margin=10),
	IntegerSliderVWidget: IntegerSliderWidgetBase.StyleSheet(
		backgroundColor=(0xae, 0xae, 0xaf), backgroundEmptyColor=(0x55, 0x56, 0x56), hoverColor=(0xce, 0xce, 0xcf),
		draggerNormalColor=(0x7e, 0x7e, 0x7f), draggerHoverColor=(0x5e, 0x5e, 0x5f), draggerDragColor=(0x3f, 0x3f, 0x3f),
		draggerMargin=5, roundCornerRadius=20, margin=10),
	LabelOverlay: LabelOverlay.StyleSheet(
		margin=0, textColor=White, fontSize=64),
	LabelWidget: LabelWidget.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0),
	IconOverlay: IconOverlay.StyleSheet(
		margin=0),
	IconWidget: IconWidget.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	LineEditWidget: LineEditWidget.StyleSheet(
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x45, 0x46, 0x46), editColor=(0x25, 0x26, 0x26),
		borderWidth=1, borderColor=(0x7e, 0x7e, 0x7f), hoverBorderColor=(0xae, 0xae, 0xaf),
		roundCornerRadius=4, margin=4,
		textIndentation=10, textColor=White,
		cursorColor=White, cursorWidth=2),
	
	IntegerLineEditWidget: IntegerLineEditWidget.StyleSheet(
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x45, 0x46, 0x46), editColor=(0x25, 0x26, 0x26),
		borderWidth=1, borderColor=(0x7e, 0x7e, 0x7f), hoverBorderColor=(0xae, 0xae, 0xaf),
		roundCornerRadius=4, margin=4,
		textIndentation=10, textColor=White,
		cursorColor=White, cursorWidth=2),
	IntegerFieldWidget: IntegerFieldWidget.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0,
		editPortion=1, sliderPortion=2),
	ConfirmationWidget: ConfirmationWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
		borderWidth=2, borderColor=(0x6e, 0x6e, 0x6f), hoverBorderColor=(0xbe, 0xbe, 0xbf),
		roundCornerRadius=16, margin=12, textMargin=5),

	
	CanvasWidget: CanvasWidget.StyleSheet(
		backgroundColor=(0x2e, 0x2e, 0x2f), hoverColor=(0x2e, 0x2e, 0x2f),
		roundCornerRadius=0, margin=0),
	SidebarWidget: SidebarWidget.StyleSheet(
		backgroundColor=(0x47, 0x47, 0x47), hoverColor=(0x47, 0x47, 0x47),
		roundCornerRadius=0, margin=0),
	ConfigHEntryBase: ConfigHEntryBase.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0),
	ConfigSectionContent: ConfigSectionContent.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0),
	ConfigSection: ConfigSection.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=10,
		fontColor=White, lineColor=(0xff, 0xff, 0xff), lineWidth=2),
	ConfigPanel: ConfigPanel.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0,
		scrollVel=20),
	ConfigWidget: ConfigWidget.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0),

	ColorPickerHue: ColorPickerHue.StyleSheet(
		draggerNormalColor=(0x7e, 0x7e, 0x7f), draggerHoverColor=(0x5e, 0x5e, 0x5f), draggerDragColor=(0x3f, 0x3f, 0x3f),
		draggerMargin=0, roundCornerRadius=0, margin=5),
	ColorPickerSV: ColorPickerSV.StyleSheet(
		roundCornerRadius=0, margin=5),
	ColorPickerSetter: ColorPickerSetter.StyleSheet(),
	ColorPickerWidgetContent: ColorPickerWidgetContent.StyleSheet(),


	ApplicationWidget: ApplicationWidget.StyleSheet()
}