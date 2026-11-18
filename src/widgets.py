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

def setEditStateCb_impl(w: IconedPushButtonWidget, state: EditStateTag):
	if w.uniform.editStateTag[-1] != state:
		w.uniform.editStateTag.append(state)
	else: w.uniform.editStateTag.pop()
	w.uniform.app.editStateUpdate()

@dataclass(slots=True)
class HeightedIconedPushButtonWidget(IconedPushButtonWidget):
	def reportHeight(self): return 2
	def activateLayout(self):
		if (self.dim.y == 0): return
		return super().activateLayout()

@dataclass(slots=True)
class SidebarWidget(ScrollLayout):

	def addTool_impl(self, icon: str, state: EditStateTag):
		image = pygame.image.load(getProgramDir() / icon).convert_alpha()
		with pygame.PixelArray(image) as pixels:
			pixels.replace((0, 0, 0), (255, 255, 255), 0.0)
		return self.addWidget(
			UnitedLinearLayoutAttribute(),
		    HeightedIconedPushButtonWidget,
			source=image,
			onPress=lambda w: setEditStateCb_impl(w, state))

	# ================ Contract Interface ================

	def __post_init__(self):
		self.addTool_impl("assets/stroke-tool-icon.png", EditStateTag.Stroke)

	def activateLayout(self):
		if (self.dim.y == 0): return
		#proportion: float = self.dim.x / self.dim.y
		#for attrib in self.solver.widgetAttribs:
		#	attrib.proportion = proportion
		return super().activateLayout()

	def draw(self, screen):
		RectWidgetBase.draw(self, screen)
		super().draw(screen)

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
class ConfigPanel(ScrollLayout):
	'''
	Container of Sections.
	All sub widgets must be sections. (with exceptions)
	'''

	# ================ Contract Interface ================
	
	def draw(self, screen):
		RectWidgetBase.draw(self, screen)
		super().draw(screen)

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
	s = delta / v if v != 0 else 0.0 # saturation
	# Color = Brightness * (White * (1 - Saturation) + Hue * Saturation)
	h = (int((r - cmin) / delta * 255),
		 int((g - cmin) / delta * 255),
		 int((b - cmin) / delta * 255)) if delta != 0 else (255, 0, 0)
	return (h, s, v)

# hsv -> rgb
def findRGB(h: Color, s: float, v: float) -> tuple[int, int, int]:
    # Color = Brightness * (White * (1 - Saturation) + Hue * Saturation)
	w = 255.0 * (1.0 - s)
	
	return (
	    int(v * (w + h[0] * s)),
	    int(v * (w + h[1] * s)),
	    int(v * (w + h[2] * s))
	)

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

def setColorV(color: Color, value: float):
	h, s, v = findHSV(color)
	return findRGB(h, s, value)

def brighter(color: Color, value: float):
	h, s, v = findHSV(color)
	return findRGB(h, s, min(1.0, v + value))
def darker(color: Color, value: float):
	h, s, v = findHSV(color)
	return findRGB(h, s, max(0.0, v - value))


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
	onCancel: Callable[[], None] | Callable[[Self], None] = lambda: None

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
		self.sv.setSV(s, v)
		self.sv.setHue(h)

	def interfaceSetColor_impl(self):
		self.setter.setColor(self.color)

	def setColor(self, color: Color):
		self.color = color
		self.pickerSetColor_impl()
		self.setter.setColor(color)


	def handleConfirmAction_impl(self):
		if (self.confirm.confirmed): optionalCall(self.onConfirm, self)
		else:                        optionalCall(self.onCancel , self)

	# ================ Contract Interface ================

	def __post_init__(self):
		self.sv      = self.addWidget(UnitedLinearLayoutAttribute(order=0), ColorPickerSV     , onColorChange=self.handleSVChange          )
		self.hue     = self.addWidget(UnitedLinearLayoutAttribute(order=1), ColorPickerHue    , onColorChange=self.handleHueChange         )
		self.setter  = self.addWidget(UnitedLinearLayoutAttribute(order=2), ColorPickerSetter , onColorChange=self.handleColorSet          )
		self.confirm = self.addWidget(UnitedLinearLayoutAttribute(order=3), ConfirmationWidget, onAction     =self.handleConfirmAction_impl)

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
	w = section.addWidget(ColorPickerWidgetContent)
	section.content = w
	return w

# ================ Stroke ================

def configSectionStrokeGeomtry(section: ConfigSection):

	sectionAdd(section, text="Width", entryWidgetType=IntegerFieldWidget, entryWidgetArgs={"scope": (0, 100)}, proportion=(1, 2))

	section.content.addWidget(
		UnitedLinearLayoutAttribute(), ColorPickerSV)
	sectionAdd(section, text="Width", entryWidgetType=SliderHWidget, entryWidgetArgs={})
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
	configWidgets: dict[EditStateTag, ConfigPanel] = field(default_factory=dict)

	canvasWidget: CanvasWidget | None = field(init=False, default=None)
	#configWidget: ConfigWidget | None = field(init=False, default=None)
	configWidget: ConfigPanel | None = field(init=False, default=None)
	sidebarWidget: SidebarWidget | None = field(init=False, default=None)	

	def addPanel_impl(self, tag: EditStateTag):
		w = self.addWidget(
			LinearLayoutAttribute(order=1, absolute=True, visible=False, proportion=0.2), ConfigPanel)
		self.configWidgets[tag] = w
		return w

	def addSection(self, panel: ConfigPanel, sectionName: str):
		return panel.addWidget(UnitedLinearLayoutAttribute(), ConfigSection, name=sectionName)

	# ================ Initialization ================

	def initStroke_impl(self):
		panel = self.addPanel_impl(EditStateTag.Stroke)
		section = self.addSection(panel, "Stroke")
		
		def widthChange(w: IntegerFieldWidget):
			self.uniform.editState[EditStateTag.Stroke].width = w.value
		widthField: IntegerFieldWidget = sectionAdd(
			section, text="Width",
			proportion=(1, 2),
			entryWidgetType=IntegerFieldWidget,
			entryWidgetArgs={"scope": (1, 100),
							 "onValueChange": widthChange})
		self.strokeDefaultInit = lambda: widthField.setValue(
			self.uniform.editState[EditStateTag.Stroke].width)

		colorField: PushButtonWidget = sectionAdd(
			section, text="Color",
			proportion=(1, 2),
			entryWidgetType=PushButtonWidget,
			entryWidgetArgs={})
		def colorChange(color: Color):
			self.uniform.editState[EditStateTag.Stroke].color = color
			colorField.styleSheet.backgroundColor = color
			colorField.styleSheet.hoverColor = brighter(color, 0.1)
			colorField.styleSheet.pressColor = brighter(color, 0.3)
		colorField.onPress = lambda: self.requestColorPick_impl(
			lambda: self.uniform.editState[EditStateTag.Stroke].color,
			colorChange)
		colorField.styleSheet.backgroundColor = Black
		colorField.styleSheet.hoverColor = brighter(Black, 0.2)
		colorField.styleSheet.pressColor = brighter(Black, 0.5)
		colorField.styleSheet.borderWidth = 2
		colorField.styleSheet.borderColor=(0xde, 0xde, 0xdf)
		colorField.styleSheet.hoverBorderColor=(0xff, 0xff, 0xff)

	def initColorPick_impl(self):
		colorPanel = self.addPanel_impl(EditStateTag.ColorPick)
		colorSection = self.addSection(colorPanel, "Color")
		def colorCancel():
			if (self.uniform.editStateTag[-1] == EditStateTag.ColorPick): self.uniform.editStateTag.pop()
			self.editStateUpdate()
		def colorConfirm(w: IntegerFieldWidget):
			colorCancel()
			self.provideColorPick_impl()
		colorPickerContent = colorSection.addWidget(
			ColorPickerWidgetContent, onConfirm=colorConfirm, onCancel=colorCancel)
		colorSection.content = colorPickerContent
		self.colorPickProvideGetter = lambda: colorPickerContent.color
		self.colorPickProvideSetter = lambda color: colorPickerContent.setColor(color)

	def __post_init__(self):
		self.canvasWidget = self.addWidget(LinearLayoutAttribute(order=0), CanvasWidget)
		self.sidebarWidget = self.addWidget(LinearLayoutAttribute(order=2, absolute=True, proportion=0.04), SidebarWidget)

		self.initStroke_impl()
		self.initColorPick_impl()		

	# Contrainted Contract Interface
	# Will be called everytime with updated uniform state
	def editStateUpdate(self):
		if (self.uniform.editStateTag[-1] == EditStateTag.Nothing):
			self.configWidget.hide()
		else:
			tryCall(self.configWidget, "hide")
			self.configWidget = self.configWidgets[self.uniform.editStateTag[-1]]
			self.configWidget.show()

			self.configWidget.activateLayout()
			self.configWidget.activateLayout()

			self.setDefault_impl()

	# ================ Defaults ================

	def setDefault_impl(self):
		match (self.uniform.editStateTag[-1]):
			case EditStateTag.Stroke:    self.setStrokeDefault_impl()
			case EditStateTag.ColorPick: self.setColorPickDefault_impl()

	strokeDefaultInited: bool = False
	strokeDefaultInit: Callable[[], None] | None = None
	def setStrokeDefault_impl(self):
		if (not self.strokeDefaultInited):
			self.strokeDefaultInited = True
			self.strokeDefaultInit()

	def setColorPickDefault_impl(self):
		self.colorPickProvideSetter(self.colorPickRequestGetter())

	# ================ Public Interface ================

	# ---------------- Color Pick ----------------

	colorPickRequestSetter: Callable[[Color], None] | None = field(init=False, default=None)
	colorPickRequestGetter: Callable[[], Color] | None = field(init=False, default=None)
	colorPickProvideSetter: Callable[[Color], None] | None = field(init=False, default=None)
	colorPickProvideGetter: Callable[[], Color] | None = field(init=False, default=None)

	def requestColorPick_impl(self, getter: Callable[[], Color], setter: Callable[[Color], None]):
		self.uniform.editStateTag.append(EditStateTag.ColorPick)
		self.colorPickRequestGetter = getter
		self.colorPickRequestSetter = setter
		self.editStateUpdate()

	def provideColorPick_impl(self):
		self.colorPickRequestSetter(self.colorPickProvideGetter())


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
	HeightedIconedPushButtonWidget: HeightedIconedPushButtonWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
		roundCornerRadius=10, margin=10, iconMargin=5),
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