# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .widget_infrastructure import *
from .canvas_widget import *
from pathlib import Path

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
	#print(w.uniform.editStateTag)
	if (w.uniform.editStateTag[-1] == EditStateTag.Nothing):
		prevState = EditStateTag.Nothing
		w.uniform.editStateTag.append(state)
	else:
		prevState = w.uniform.editStateTag[-1]
		if (w.uniform.editStateTag[-1] == state):
			w.uniform.editStateTag.pop()
		else:
			w.uniform.editStateTag[-1] = state
	w.uniform.app.editStateUpdate(prevState)

@dataclass(slots=True)
class SidebarButtonWidget(RectWidgetBase):

	onPress:   Callable[[], None] | Callable[[Self], None] = lambda: None
	onUnpress: Callable[[], None] | Callable[[Self], None] = lambda: None

	pressing: bool = False

	# ================ Contract Interface ================

	def handleEvent(self, event):
		if (super().handleEvent(event)): return True # process sub widgets
		# sub widgets not handled - attempt handling for this widget
		# along with that, state is also modified
		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				if (not self.pressing):
					optionalCall(self.onPress, self)
					self.state.colorOverride = self.styleSheet.pressColor
					self.pressing = True
					self.diff = True
				else:
					optionalCall(self.onUnpress, self)
					self.unselect()
			case _:	return False
		return True

	def __post_init__(self):
		self.setOverlay(IconOverlay)

	def reportHeight(self): return 2

	def activateLayout(self):
		if (self.dim.y == 0): return
		self.overlay.styleSheet.margin = self.styleSheet.iconMargin + self.styleSheet.margin
		self.overlay.setImage(pygame.transform.smoothscale(
			self.source, scaleToFit(
				ivec2.fromTuple(self.source.get_size()),
			    self.dim - ivec2(self.overlay.styleSheet.margin,
			                     self.overlay.styleSheet.margin) * 2).toTuple()))

	# ================ Public Interface ================

	def unselect(self):
		self.state.colorOverride = None
		self.pressing = False
		self.diff = True

	source: pygame.Surface | None = None

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(RectWidgetBase.StyleSheet):
		pressColor: Color = DefaultColor
		iconMargin: int = 0
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class SidebarWidget(ScrollLayout):

	selected: SidebarButtonWidget | None = None

	def addTool_impl(self, icon: str, state: EditStateTag):
		def handlePress_impl(w):
			if (self.selected is not None):
				self.selected.unselect()
			self.selected = w
			setEditStateCb_impl(w, state)
		return self.addWidget(
			UnitedLinearLayoutAttribute(),
		    SidebarButtonWidget,
			source=loadIcon(icon),
			onPress=handlePress_impl,
			onUnpress=handlePress_impl)

	# ================ Contract Interface ================

	def __post_init__(self):
		self.addTool_impl("assets/file-op-icon.png", EditStateTag.FileOp)
		self.addTool_impl("assets/stroke-tool-icon.png", EditStateTag.Stroke)
		self.addTool_impl("assets/line-tool-icon.png", EditStateTag.Line)
		self.addTool_impl("assets/rect-tool-icon.png", EditStateTag.Rect)
		self.addTool_impl("assets/oval-tool-icon.png", EditStateTag.Oval)
		self.addTool_impl("assets/stamp-tool-icon.png", EditStateTag.Stamp)

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
		rect = makeRect(self.pos + ivec2(self.styleSheet.margin, self.styleSheet.margin),
								self.dim - ivec2(self.styleSheet.margin * 2, self.styleSheet.margin * 2))
		draw.rect(screen,
                  self.state.colorOverride if self.state.colorOverride is not None else
                  (self.styleSheet.hoverColor if self.state.hover else self.styleSheet.backgroundColor),
                  rect, border_radius=self.styleSheet.roundCornerRadius)
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

		prevClip = screen.get_clip()
		screen.set_clip(prevClip.clip(makeMarginedRect(self.pos, self.dim, self.styleSheet.margin)))
		self.dragger.draw(screen)
		screen.set_clip(prevClip)

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


# ################ File Explorer ################

@dataclass(slots=True)
class FileExplorerEntry(RectWidgetBase):
	selected: bool = False

	onSelectEntry: Callable[[], None] | Callable[[Self], None] = lambda: None
	onUnselectEntry: Callable[[], None] | Callable[[Self], None] = lambda: None
	onDoubleClick: Callable[[], None] | Callable[[Self], None] = lambda: None

	manifest: RectWidgetHLayout | None = field(init=False, default=None)

	path: Path | None = None

	# ================ Public Interface ================

	def unselect(self):
		self.selected = False
		self.state.colorOverride = None
		self.diff = True

	# ================ Contract Interface ================

	lastPress: int = 0
	def handleEvent(self, event: pygame.Event):
		if (super().handleEvent(event)): return True
		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				now = pygame.time.get_ticks()
				
				if (not self.selected):
					optionalCall(self.onSelectEntry, self)
					self.state.colorOverride = self.styleSheet.pressColor
					self.selected = True
				else:
					if (now - self.lastPress < 500): # double click
						optionalCall(self.onDoubleClick, self)
					else: # otherwise, unselect
						optionalCall(self.onUnselectEntry, self)
						self.state.colorOverride = None
						self.selected = False
				self.diff = True
				self.lastPress = now
			case _:	return False
		return True

	entryInfo: InitVar[Path | None] = None

	def __post_init__(self, entryInfo: Path):
		self.path = entryInfo
		self.manifest = self.addWidget(RectWidgetHLayout)
		self.manifest.addWidget(LinearLayoutAttribute(proportion=1), IconWidget).setImage(
			"assets/file-icon.png" if entryInfo.is_file() else "assets/dir-icon.png")
		label = self.manifest.addWidget(LinearLayoutAttribute(proportion=7), LabelWidget, text=entryInfo.name)
		label.overlay.styleSheet.fontSize = int(self.uniform.fontSize * 0.5)

	def activateLayout(self):
		self.manifest.pos = replace(self.pos)
		self.manifest.dim = replace(self.dim)
		super().activateLayout()

	def reportHeight(self): return 1

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(PushButtonWidget.StyleSheet):
		pressColor: Color = DefaultColor
		selectedColor: Color = DefaultColor
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class FileExplorerExplorer(ScrollLayout):
	'''File directory visualizer. Btw, I refuse to give up the name ExplorerExplorer.'''

	selectedEntry: FileExplorerEntry | None = None

	onPathChange: Callable[[Path], None] = lambda p: None
	onSelection:  Callable[[Path], None] = lambda p: None

	def handleSelection_impl(self, w: FileExplorerEntry):
		if (self.selectedEntry is not None):
			self.selectedEntry.unselect()
		self.selectedEntry = w
		self.onSelection(w.path)
	def handleUnselection_impl(self, w: FileExplorerEntry):
		self.selectedEntry = None

	def handleDoubleClick_impl(self, w: FileExplorerEntry):
		self.onPathChange(w.path)

	# ================ Public Interface ================

	def setPath(self, path: Path):
		# clear
		self.widgets.clear()
		self.solver.widgetAttribs.clear()
		self.selectedEntry = None

		contents = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
		for i in contents:
			self.addWidget(
				UnitedLinearLayoutAttribute(), FileExplorerEntry, entryInfo=i,
				onSelectEntry  =self.handleSelection_impl,
				onDoubleClick  =self.handleDoubleClick_impl,
				onUnselectEntry=self.handleUnselection_impl)

		self.activateLayout()
		self.activateLayout()

		self.diff = True

	# ================ Contract Interface ================

	def activateLayout(self):
		if (self.dim.y == 0): return
		return super().activateLayout()

	def draw(self, screen):
		rect = makeRect(self.pos + ivec2(self.styleSheet.margin, self.styleSheet.margin),
						self.dim - ivec2(self.styleSheet.margin * 2, self.styleSheet.margin * 2))
		pygame.draw.rect(screen,
		          self.state.colorOverride if self.state.colorOverride is not None else
				  (self.styleSheet.hoverColor if self.state.hover else self.styleSheet.backgroundColor),
		          rect, border_radius=self.styleSheet.roundCornerRadius)
		super().draw(screen)

@dataclass(slots=True)
class FileExplorerWidgetContent(RectWidgetVLayout):
	# widgets
	forwardButton:  IconedPushButtonWidget | None = field(init=False, default=None)
	backwardButton: IconedPushButtonWidget | None = field(init=False, default=None)
	pathBar:        LineEditWidget         | None = field(init=False, default=None)
	explorer:       FileExplorerExplorer   | None = field(init=False, default=None)
	resultBar:      LineEditWidget         | None = field(init=False, default=None)

	confirm: ConfirmationWidget | None = field(init=False, default=None)

	# state
	path: Path = field(default_factory=Path.home)
	history: list[Path] = field(default_factory=lambda: [Path.home()])
	historyIndex: int = 0

	resultPath: Path | None = None # public interface for others to inspect
	defaultResult: str | None = None # only used for selecting save destination

	# interface
	onConfirm: Callable[[], None] | Callable[[Self], None] = lambda: None
	onCancel:  Callable[[], None] | Callable[[Self], None] = lambda: None

	# call after self.path is set
	def updatePath_impl(self):
		self.explorer.setPath(self.path)
		self.pathBar.setText(str(self.path.absolute()))
		self.resultBar.setText(str((self.path / self.defaultResult if self.defaultResult is not None else self.path).absolute()))

	def forwardHistory_impl(self):
		if (self.historyIndex == len(self.history) - 1): return
		self.historyIndex += 1
		self.path = self.history[self.historyIndex]
		self.updatePath_impl()
		
	def backwardHistory_impl(self):
		if (self.historyIndex == 0): return
		self.historyIndex -= 1
		self.path = self.history[self.historyIndex]
		self.updatePath_impl()

	# call after self.path is set; don't call when forward/backwarding
	def enterDir_impl(self):
		self.historyIndex += 1
		self.history = self.history[:self.historyIndex]
		self.history.append(self.path)

	def handleExplorerPathChange_impl(self, path: Path):
		'''Double click'''
		if (path.is_dir()):
			self.path = path
			self.updatePath_impl()
			self.enterDir_impl()
		else:
			self.resultPath = path
			optionalCall(self.onConfirm, self)

	def handlePathSelection_impl(self, path: Path):
		self.resultPath = path
		self.resultBar.setText(str(path.absolute()))

	# ================ Contract Interface ================

	def __post_init__(self):
		navigationLayout: RectWidgetHLayout = self.addWidget(
			LinearLayoutAttribute(proportion=0.05, absolute=True), RectWidgetHLayout)
		self.backwardButton = navigationLayout.addWidget(
			LinearLayoutAttribute(proportion=0.15, absolute=True), IconedPushButtonWidget,
			source=loadIcon("assets/backward-icon.png"),
			onPress=self.backwardHistory_impl)
		self.backwardButton.styleSheet = IconedPushButtonWidget.StyleSheet(
			backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
			borderWidth=2, borderColor=(0x6e, 0x6e, 0x6f), hoverBorderColor=(0xbe, 0xbe, 0xbf),
			roundCornerRadius=8, margin=2, iconMargin=2)
		self.backwardButton.styleSheet.margin = 2
		self.backwardButton.styleSheet.iconMargin = 2
		self.forwardButton = navigationLayout.addWidget(
			LinearLayoutAttribute(proportion=0.15, absolute=True), IconedPushButtonWidget,
			source=loadIcon("assets/forward-icon.png"),
			onPress=self.forwardHistory_impl)
		self.forwardButton.styleSheet = IconedPushButtonWidget.StyleSheet(
			backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
			borderWidth=2, borderColor=(0x6e, 0x6e, 0x6f), hoverBorderColor=(0xbe, 0xbe, 0xbf),
			roundCornerRadius=8, margin=2, iconMargin=2)
		def handlePathBarEditComplete():
			path = Path(self.pathBar.text)
			if (not path.exists()): return
			self.path = path
			self.updatePath_impl()
			self.enterDir_impl()
		self.pathBar = navigationLayout.addWidget(
			LinearLayoutAttribute(), LineEditWidget,
			onEditComplete=handlePathBarEditComplete)

		self.explorer = self.addWidget(
			LinearLayoutAttribute(), FileExplorerExplorer,
			onPathChange=self.handleExplorerPathChange_impl,
			onSelection=self.handlePathSelection_impl)
		self.explorer.setPath(self.path)

		self.resultBar = self.addWidget(
			LinearLayoutAttribute(proportion=0.05, absolute=True), LineEditWidget)
		self.resultBar.setText(str((self.path / self.defaultResult if self.defaultResult is not None else self.path).absolute()))
		
		def handleConfirmAction():
			self.defaultResult = None
			if (self.confirm.confirmed):
				# if (self.explorer.selectedEntry is None):
				# 	if (self.defaultResult is None): return
				# else: self.resultPath = self.explorer.selectedEntry.path
				self.resultPath = Path(self.resultBar.text)
				#print(self.resultPath)
				optionalCall(self.onConfirm, self)
			else: optionalCall(self.onCancel, self)

		self.confirm = self.addWidget(
			LinearLayoutAttribute(proportion=0.075, absolute=True), ConfirmationWidget,
			onAction=handleConfirmAction)

	def activateLayout(self):
		if (self.dim.y == 0): return
		self.pathBar.setText(str(self.path))
		return super().activateLayout()

	# ================ Public Interface ================

	def setPath(self, path: Path):
		self.path = path
		self.updatePath_impl()

	def reset(self):
		self.setPath(Path.home())
		self.historyIndex = 0
		self.history = [Path.home()]

# ################ Stamp Library ################

@dataclass(slots=True)
class StampLibraryEntry(RectWidgetBase):
	selected: bool = False

	onSelectEntry: Callable[[], None] | Callable[[Self], None] = lambda: None
	onUnselectEntry: Callable[[], None] | Callable[[Self], None] = lambda: None

	textureId: int | None = None

	# ================ Public Interface ================

	def unselect(self):
		self.selected = False
		self.state.colorOverride = None
		self.diff = True

	# ================ Contract Interface ================

	def handleEvent(self, event: pygame.Event):
		if (super().handleEvent(event)): return True
		match (event.type):
			case pygame.MOUSEBUTTONDOWN:
				if (event.button != 1): return False
				
				if (not self.selected):
					optionalCall(self.onSelectEntry, self)
					self.state.colorOverride = self.styleSheet.pressColor
					self.selected = True
				else:
					optionalCall(self.onUnselectEntry, self)
					self.state.colorOverride = None
					self.selected = False
				self.diff = True
			case _:	return False
		return True

	def __post_init__(self):
		self.setOverlay(IconOverlay)
		self.overlay.styleSheet.margin = 10

	def activateLayout(self):
		if (self.dim.y == 0): return
		self.overlay.texture = pygame.transform.smoothscale(
			self.uniform.engine.stampTextureData[self.textureId],
			scaleToFit(
				ivec2.fromTuple(self.uniform.engine.stampTextureData[self.textureId].get_size()),
				self.dim - ivec2(2 * self.overlay.styleSheet.margin)).toTuple())
		super().activateLayout()

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(PushButtonWidget.StyleSheet):
		pressColor: Color = DefaultColor
		selectedColor: Color = DefaultColor
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

@dataclass(slots=True)
class StampLibraryLineEntry(RectWidgetHLayout):
	a: StampLibraryEntry | None = field(init=False, default=None)
	b: StampLibraryEntry | None = field(init=False, default=None)

	# ================ Contract Interface ================

	def reportHeight(self): return 3

	# ================ Public Interface ================
	
	def setTextures(self, textureIda: int, textureIdb: int):
		self.a = self.addWidget(LinearLayoutAttribute(proportion=0.5, absolute=True), StampLibraryEntry, textureId=textureIda)
		if (len(self.uniform.engine.stampTextureData) == textureIdb): return
		self.b = self.addWidget(LinearLayoutAttribute(), StampLibraryEntry, textureId=textureIdb)
	
	def setCallbacks(self, se, ue):
		self.a.onSelectEntry = se
		self.a.onUnselectEntry = ue
		if (self.b is not None):
			self.b.onSelectEntry = se
			self.b.onUnselectEntry = ue

@dataclass(slots=True)
class StampLibraryExplorer(ScrollLayout):

	selectedEntry: StampLibraryEntry | None = None

	onSelectEntry: Callable[[StampLibraryEntry], None] = lambda w: None
	onUnselectEntry: Callable[[StampLibraryEntry], None] = lambda w: None

	def handleSelectEntry_impl(self, w: StampLibraryEntry):
		if (self.selectedEntry is not None):
			self.selectedEntry.unselect()
		self.selectedEntry = w
		self.onSelectEntry(w)

	def handleUnselectEntry_impl(self, w: StampLibraryEntry):
		self.selectedEntry = None
		self.onUnselectEntry(w)

	# ================ Contract Interface ================

	def reportHeight(self): return 8
	def draw(self, screen):
		draw.rect(screen,
				  self.state.colorOverride if self.state.colorOverride is not None else
				  (self.styleSheet.hoverColor if self.state.hover else self.styleSheet.backgroundColor),
				  makeRect(self.pos + ivec2(self.styleSheet.margin, self.styleSheet.margin),
										self.dim - ivec2(self.styleSheet.margin * 2, self.styleSheet.margin * 2)),
				  border_radius=self.styleSheet.roundCornerRadius)
		super().draw(screen)

	# ================ Public Interface ================
	
	def clear(self):
		self.widgets.clear()
		self.solver.widgetAttribs.clear()
		self.selectedEntry = None

	def present(self):
		self.clear()

		for i in range(0, len(self.uniform.engine.stampTextureData), 2):
			entry = self.addWidget(UnitedLinearLayoutAttribute(), StampLibraryLineEntry)
			entry.setTextures(i, i + 1)
			entry.setCallbacks(self.handleSelectEntry_impl, self.handleUnselectEntry_impl)
	
@dataclass(slots=True)
class StampLibraryWidgetContent(RectWidgetVLayout):
	# widgets
	addButton: LabeledPushButtonWidget | None = field(init=False, default=None)
	explorer:  StampLibraryExplorer | None = field(init=False, default=None)

	requestFileExploreCb: Callable[[Callable[[Path], None]], None] | None = None

	def handleSelectEntry_impl(self, w: StampLibraryEntry):
		self.uniform.editState[EditStateTag.Stamp].textureId = w.textureId

	def handleUnselectEntry_impl(self, w: StampLibraryEntry):
		self.uniform.editState[EditStateTag.Stamp].textureId = -1


	def handleFileExplore_impl(self, path: Path):
		if (path.is_dir() or path.suffix.lower() not in (".png", ".jpg", ".bmp")): return
		self.uniform.engine.stampTextureData.append(
			pygame.transform.smoothscale(
				(texture := pygame.image.load(str(path)).convert_alpha()),
				scaleToFit(ivec2.fromTuple(texture.get_size()), ivec2(320, 320)).toTuple()))
		self.explorer.present()
		self.activateLayout()
		self.activateLayout()

	# ================ Contract Interface ================

	def __post_init__(self):
		self.addButton = self.addWidget(
			LinearLayoutAttribute(proportion=0.16, absolute=True),
			LabeledPushButtonWidget, text="Add",
			onPress=lambda: self.requestFileExploreCb(self.handleFileExplore_impl))
		self.addButton.overlay.styleSheet.fontSize = int(self.uniform.fontSize * 0.7)
		self.addButton.styleSheet = LabeledPushButtonWidget.StyleSheet(
			backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
			borderWidth=2, borderColor=(0x6e, 0x6e, 0x6f), hoverBorderColor=(0xbe, 0xbe, 0xbf),
			roundCornerRadius=8, margin=4, textMargin=2)
		self.explorer = self.addWidget(
			LinearLayoutAttribute(), StampLibraryExplorer,
			onSelectEntry=self.handleSelectEntry_impl,
			onUnselectEntry=self.handleUnselectEntry_impl)

	def reportHeight(self):
		return self.explorer.reportHeight()




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
def sectionAddInvisible(section: ConfigSection, *args, **kwargs):
	return section.content.addWidget(
		UnitedLinearLayoutAttribute(visible=False), ConfigHEntryBase,
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
	# tools
	configSections: dict[EditStateTag, ConfigSection] = field(default_factory=dict)
	toolActivationCallback: dict[EditStateTag, Callable[[], None]] = field(default_factory=dict)
	toolDeactivationCallback: dict[EditStateTag, Callable[[], None]] = field(default_factory=dict)

	# panels
	mainPanel:         ConfigPanel   | None = field(init=False, default=None)
	colorPickPanel:    ConfigPanel   | None = field(init=False, default=None)
	fileExplorerPanel: RectWidgetHolder | None = field(init=False, default=None)

	# main widgets
	canvasWidget: CanvasWidget | None = field(init=False, default=None)
	configWidget: ConfigPanel | None = field(init=False, default=None)
	sidebarWidget: SidebarWidget | None = field(init=False, default=None)	

	# ================ Implementation Utility ================

	def addPanel_impl(self):
		w = self.addWidget(
			LinearLayoutAttribute(order=1, absolute=True, visible=False, proportion=0.2), ConfigPanel)
		return w

	def addSection_impl(self, panel: ConfigPanel, sectionName: str, tag: EditStateTag):
		w = panel.addWidget(UnitedLinearLayoutAttribute(), ConfigSection, name=sectionName)
		self.configSections[tag] = w
		return w

	def switchPanel_impl(self, panel: ConfigPanel):
		self.configWidget.hide()
		self.configWidget = panel
		self.editStateUpdate()

	# ================ Initialization Untilities ================

	def initAddColorField_impl(self, section: ConfigSection, tag: EditStateTag):
		colorField: PushButtonWidget = sectionAdd(
			section, text="Color",
			proportion=(1, 2),
			entryWidgetType=PushButtonWidget,
			entryWidgetArgs={})
		def colorChange(color: Color):
			self.uniform.editState[tag].color = color
			colorField.styleSheet.backgroundColor = color
			colorField.styleSheet.hoverColor = brighter(color, 0.1)
			colorField.styleSheet.pressColor = brighter(color, 0.3)
		colorField.onPress = lambda: self.requestColorPick_impl(
			lambda: self.uniform.editState[tag].color,
			colorChange)
		colorField.styleSheet.backgroundColor = Black
		colorField.styleSheet.hoverColor = brighter(Black, 0.2)
		colorField.styleSheet.pressColor = brighter(Black, 0.5)
		colorField.styleSheet.borderWidth = 2
		colorField.styleSheet.borderColor=(0xde, 0xde, 0xdf)
		colorField.styleSheet.hoverBorderColor=(0xff, 0xff, 0xff)

	def initEraseToggle_impl(self, section: ConfigSection, tag: EditStateTag):
		def handleToggle(w: ToggleWidget):
			if (w.on):
				self.uniform.editState[tag].colorOverride = White
			else: self.uniform.editState[tag].colorOverride = None

		toggle: ToggleWidget = sectionAdd(
			section, text="Erase",
			proportion=(1, 2),
			entryWidgetType=ToggleWidget,
			entryWidgetArgs={"onToggle": handleToggle}
		)

	# ================ Initialization ================

	def initStroke_impl(self):
		section = self.addSection_impl(self.mainPanel, "Stroke", EditStateTag.Stroke)

		def activate():
			self.uniform.engine.strokeSetPreview(
				self.uniform.editState[EditStateTag.Stroke])
		def deactivate():
			self.uniform.engine.strokeStopPreview()
		
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

		self.initAddColorField_impl(section, EditStateTag.Stroke)
		self.initEraseToggle_impl(section, EditStateTag.Stroke)

		self.toolActivationCallback[EditStateTag.Stroke] = activate
		self.toolDeactivationCallback[EditStateTag.Stroke] = deactivate

	def initLine_impl(self):
		section = self.addSection_impl(self.mainPanel, "Line", EditStateTag.Line)

		def activate():
			self.uniform.engine.lineSetNormalPreview(
				self.uniform.editState[EditStateTag.Line])
		def deactivate():
			self.uniform.engine.lineStopNormalPreview()
		
		def widthChange(w: IntegerFieldWidget):
			self.uniform.editState[EditStateTag.Line].width = w.value
		widthField: IntegerFieldWidget = sectionAdd(
			section, text="Width",
			proportion=(1, 2),
			entryWidgetType=IntegerFieldWidget,
			entryWidgetArgs={"scope": (1, 100),
							 "onValueChange": widthChange})
		self.lineDefaultInit = lambda: widthField.setValue(
			self.uniform.editState[EditStateTag.Line].width)

		self.initAddColorField_impl(section, EditStateTag.Line)
		self.initEraseToggle_impl(section, EditStateTag.Line)

		self.toolActivationCallback[EditStateTag.Line] = activate
		self.toolDeactivationCallback[EditStateTag.Line] = deactivate

	rectDefaultInited: bool = False
	def initRect_impl(self):
		section = self.addSection_impl(self.mainPanel, "Rectangle", EditStateTag.Rect)

		hollowToggle: ToggleWidget = sectionAdd(
			section, text="Hollow",
			proportion=(1, 2),
			entryWidgetType=ToggleWidget,
			entryWidgetArgs={})

		def handleWidthValueChange(w: IntegerFieldWidget):
			self.uniform.editState[EditStateTag.Rect].hollowWidth = w.value

		hollowWidthEntry = section.content.addWidget(
			UnitedLinearLayoutAttribute(visible=False), ConfigHEntryBase,
			text="     Width", proportion=(1, 2),
			entryWidgetType=IntegerFieldWidget,
		 	entryWidgetArgs={"scope": (1, 100),
		 					 "onValueChange": handleWidthValueChange})
		hollowWidthEntry.labelWidget.overlay.styleSheet.fontSize = int(
			hollowWidthEntry.labelWidget.overlay.styleSheet.fontSize * 0.8)

		def handleToggle(w: ToggleWidget):
			self.uniform.editState[EditStateTag.Rect].hollow = w.on
			# show/hide linked widget
			if (w.on): hollowWidthEntry.show()
			else: hollowWidthEntry.hide()
			self.mainPanel.activateLayout()
			self.mainPanel.activateLayout()
			self.mainPanel.resetScroll()
			self.mainPanel.activateLayout()
			self.mainPanel.activateLayout()
			self.mainPanel.scrollToWidget(section)
			if (not self.rectDefaultInited):
				self.rectDefaultInited = True
				hollowWidthEntry.entryWidget.setValue(20)
				self.uniform.editState[EditStateTag.Rect].hollowWidth = 20
			self.diff = True
		hollowToggle.onToggle = handleToggle

		self.rectDefaultInit = lambda: None

		self.initAddColorField_impl(section, EditStateTag.Rect)
		self.initEraseToggle_impl(section, EditStateTag.Rect)

	ovalDefaultInited: bool = False
	def initOval_impl(self):
		section = self.addSection_impl(self.mainPanel, "Oval", EditStateTag.Oval)

		hollowToggle: ToggleWidget = sectionAdd(
			section, text="Hollow",
			proportion=(1, 2),
			entryWidgetType=ToggleWidget,
			entryWidgetArgs={})

		def handleWidthValueChange(w: IntegerFieldWidget):
			self.uniform.editState[EditStateTag.Oval].hollowWidth = w.value

		hollowWidthEntry = section.content.addWidget(
			UnitedLinearLayoutAttribute(visible=False), ConfigHEntryBase,
			text="     Width", proportion=(1, 2),
			entryWidgetType=IntegerFieldWidget,
		 	entryWidgetArgs={"scope": (1, 100),
		 					 "onValueChange": handleWidthValueChange})
		hollowWidthEntry.labelWidget.overlay.styleSheet.fontSize = int(
			hollowWidthEntry.labelWidget.overlay.styleSheet.fontSize * 0.8)

		def handleToggle(w: ToggleWidget):
			self.uniform.editState[EditStateTag.Oval].hollow = w.on
			# show/hide linked widget
			if (w.on): hollowWidthEntry.show()
			else: hollowWidthEntry.hide()
			self.mainPanel.activateLayout()
			self.mainPanel.activateLayout()
			self.mainPanel.resetScroll()
			self.mainPanel.activateLayout()
			self.mainPanel.activateLayout()
			self.mainPanel.scrollToWidget(section)
			if (not self.ovalDefaultInited):
				self.ovalDefaultInited = True
				hollowWidthEntry.entryWidget.setValue(20)
				self.uniform.editState[EditStateTag.Oval].hollowWidth = 20
			self.diff = True
		hollowToggle.onToggle = handleToggle

		self.ovalDefaultInit = lambda: None

		self.initAddColorField_impl(section, EditStateTag.Oval)
		self.initEraseToggle_impl(section, EditStateTag.Oval)

	def initStamp_impl(self):
		section = self.addSection_impl(self.mainPanel, "Stamp", EditStateTag.Stamp)
		
		def activate():
			self.uniform.engine.stampSetPreview(
				self.uniform.editState[EditStateTag.Stamp])
		def deactivate():
			self.uniform.engine.stampStopPreview()
						
		def scaleChange(w: IntegerFieldWidget):
			self.uniform.editState[EditStateTag.Stamp].scale = w.value / 100
			activate()
		scaleField: IntegerFieldWidget = sectionAdd(
			section, text="Scale",
			proportion=(1, 2),
			entryWidgetType=IntegerFieldWidget,
			entryWidgetArgs={"scope": (1, 300),
							 "onValueChange": scaleChange})

		self.toolActivationCallback[EditStateTag.Stamp] = activate
		self.toolDeactivationCallback[EditStateTag.Stamp] = deactivate

		# Default Stamps

		for i in (getProgramDir() / "assets/stamp-builtin").iterdir():
			self.uniform.engine.stampTextureData.append(
				pygame.transform.smoothscale(
					(texture := pygame.image.load(str(i)).convert_alpha()),
					scaleToFit(ivec2.fromTuple(texture.get_size()), ivec2(320, 320)).toTuple()))

		# Stamp Library

		librarySection = section.content.addWidget(
			UnitedLinearLayoutAttribute(), ConfigSection,
			name="Library")
		libraryContent = librarySection.addWidget(
			StampLibraryWidgetContent,
			requestFileExploreCb=self.requestFileExplore_impl)
		librarySection.content = libraryContent

		libraryContent.explorer.present()

		def default():
			scaleField.setValue(
				int(self.uniform.editState[EditStateTag.Stamp].scale * 100))
		self.stampDefaultInit = default

	def initFileOp_impl(self):
		section = self.addSection_impl(self.mainPanel, "File", EditStateTag.FileOp)

		def handleNew():
			self.canvasWidget.clear()
		def handleOpen():
			def open(path: Path):
				self.uniform.engine.read(path)
				self.canvasWidget.diff = True
			self.requestFileExplore_impl(open)
		def handleSave():
			self.setFileExploreDefaultResult("image.ev")
			self.requestFileExplore_impl(self.uniform.engine.write)
		def handleExport():
			self.setFileExploreDefaultResult("image.png")
			self.requestFileExplore_impl(self.uniform.engine.export)

		# this really shows how desperate I am at this point
		@dataclass(slots=True)
		class MyLabeledPushButtonWidget(LabeledPushButtonWidget):
			def reportHeight(self): return 1.5
			def __post_init__(self):
				super().__post_init__()
				self.overlay.styleSheet.fontSize = int(self.uniform.fontSize * 0.7)

		styleSheet = LabeledPushButtonWidget.StyleSheet(
			backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
			borderWidth=2, borderColor=(0x6e, 0x6e, 0x6f), hoverBorderColor=(0xbe, 0xbe, 0xbf),
			roundCornerRadius=16, margin=6, textMargin=5)
		
		section.content.addWidget(UnitedLinearLayoutAttribute(), MyLabeledPushButtonWidget, text="New",    onPress=handleNew   ).styleSheet = styleSheet
		section.content.addWidget(UnitedLinearLayoutAttribute(), MyLabeledPushButtonWidget, text="Open",   onPress=handleOpen  ).styleSheet = styleSheet
		section.content.addWidget(UnitedLinearLayoutAttribute(), MyLabeledPushButtonWidget, text="Save",   onPress=handleSave  ).styleSheet = styleSheet
		section.content.addWidget(UnitedLinearLayoutAttribute(), MyLabeledPushButtonWidget, text="Export", onPress=handleExport).styleSheet = styleSheet

	def initColorPick_impl(self):
		self.colorPickPanel = self.addPanel_impl()
		section = self.colorPickPanel.addWidget(UnitedLinearLayoutAttribute(), ConfigSection, name="Color Picker")
		
		def cancel():
			if (self.uniform.editStateTag[-1] == EditStateTag.ColorPick):
				self.uniform.editStateTag.pop()
			self.isOrdinaryPanelState = True
			self.switchPanel_impl(self.mainPanel)
		def confirm(w: IntegerFieldWidget):
			cancel()
			self.provideColorPick_impl()
		content = section.addWidget(
			ColorPickerWidgetContent, onConfirm=confirm, onCancel=cancel)
		section.content = content
		self.colorPickProvideGetter = lambda: content.color
		self.colorPickProvideSetter = lambda color: content.setColor(color)

	def initFileExplorer_impl(self):
		self.fileExplorerPanel = self.addWidget(
			LinearLayoutAttribute(order=1, absolute=True, visible=False, proportion=0.2),
			RectWidgetHolder)
		
		section = self.fileExplorerPanel.addWidget(ConfigSection, name="File Explorer")
		self.fileExplorerPanel.content = section
		
		def cancel(): # close session
			if (self.uniform.editStateTag[-1] == EditStateTag.FileExplore):
				self.uniform.editStateTag.pop()
			self.isOrdinaryPanelState = True
			content.reset()
			self.switchPanel_impl(self.mainPanel)
		def confirm():
			cancel()
			self.provideFileExplore_impl()
		content = section.addWidget(FileExplorerWidgetContent, onCancel=cancel, onConfirm=confirm)
		section.content = content

		self.fileExplorerProvideGetter = lambda: content.resultPath
		def setDefault(name: str):
			content.defaultResult = name
		self.fileExplorerDefaultSetter = setDefault
		self.fileExplorerResetter = content.reset

	def __post_init__(self):
		self.canvasWidget = self.addWidget(LinearLayoutAttribute(order=0), CanvasWidget)
		self.sidebarWidget = self.addWidget(LinearLayoutAttribute(order=2, absolute=True, proportion=0.04), SidebarWidget)

		self.initColorPick_impl()
		self.initFileExplorer_impl()

		self.mainPanel = self.addPanel_impl()
		self.configWidget = self.mainPanel
		self.initFileOp_impl()
		self.initStroke_impl()
		self.initLine_impl()
		self.initRect_impl()
		self.initOval_impl()
		self.initStamp_impl()

	isOrdinaryPanelState: bool = True

	# Contrainted Contract Interface
	# Will be called everytime with updated uniform state
	def editStateUpdate(self, prevState: EditStateTag = EditStateTag.Nothing):
		if (prevState in self.toolDeactivationCallback):
			self.toolDeactivationCallback[prevState]()

		if (self.uniform.editStateTag[-1] == EditStateTag.Nothing):
			self.configWidget.hide()
		else:
			if (self.isOrdinaryPanelState):
				self.configWidget = self.mainPanel

			self.configWidget.show()
			self.configWidget.activateLayout()
			self.configWidget.activateLayout()
			if (self.isOrdinaryPanelState):
				self.configWidget.scrollToWidget(self.configSections[self.uniform.editStateTag[-1]])
				if (self.uniform.editStateTag[-1] in self.toolActivationCallback):
					self.toolActivationCallback[self.uniform.editStateTag[-1]]()

			self.setDefault_impl()

	# ================ Defaults ================

	defaultInited: bool = False
	def setDefault_impl(self):
		if (self.isOrdinaryPanelState):
			if (self.defaultInited): return
			self.defaultInited = True
			self.strokeDefaultInit()
			self.rectDefaultInit()
			self.stampDefaultInit()
			self.lineDefaultInit()
			self.ovalDefaultInit()
			
		else:
			match (self.uniform.editStateTag[-1]):
				case EditStateTag.ColorPick: self.setColorPickDefault_impl()

	strokeDefaultInit: Callable[[], None] | None = None
	rectDefaultInit:   Callable[[], None] | None = None
	stampDefaultInit:  Callable[[], None] | None = None
	lineDefaultInit:  Callable[[], None] | None = None
	ovalDefaultInit:  Callable[[], None] | None = None

	def setColorPickDefault_impl(self):
		self.colorPickProvideSetter(self.colorPickRequestGetter())

	# ================ Signal Network ================

	# ---------------- Color Pick ----------------

	colorPickRequestSetter: Callable[[Color], None] | None = field(init=False, default=None)
	colorPickRequestGetter: Callable[[], Color] | None = field(init=False, default=None)
	colorPickProvideSetter: Callable[[Color], None] | None = field(init=False, default=None)
	colorPickProvideGetter: Callable[[], Color] | None = field(init=False, default=None)

	def requestColorPick_impl(self, getter: Callable[[], Color], setter: Callable[[Color], None]):
		self.uniform.editStateTag.append(EditStateTag.ColorPick)
		self.colorPickRequestGetter = getter
		self.colorPickRequestSetter = setter
		self.isOrdinaryPanelState = False
		self.switchPanel_impl(self.colorPickPanel)

	def provideColorPick_impl(self):
		self.colorPickRequestSetter(self.colorPickProvideGetter())

	# ---------------- File Explore ----------------

	fileExplorerRequestSetter: Callable[[Path], None] | None = field(init=False, default=None)
	fileExplorerProvideGetter: Callable[[], Path] | None = field(init=False, default=None)

	def requestFileExplore_impl(self, setter: Callable[[Path], None]):
		self.uniform.editStateTag.append(EditStateTag.FileExplore)
		self.fileExplorerRequestSetter = setter
		self.isOrdinaryPanelState = False
		self.fileExplorerResetter()
		self.switchPanel_impl(self.fileExplorerPanel)

	def provideFileExplore_impl(self):
		self.fileExplorerRequestSetter(self.fileExplorerProvideGetter())

	fileExplorerDefaultSetter:   Callable[[str], None] | None = field(init=False, default=None)
	fileExplorerResetter:        Callable[[]   , None] | None = field(init=False, default=None)

	def setFileExploreDefaultResult(self, name: str):
		self.fileExplorerDefaultSetter(name)
	

theme: WidgetTheme = {

	RectWidgetBase: RectWidgetBase.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	TransparentRectWidget: TransparentRectWidget.StyleSheet(),
	RectWidgetHLayout: RectWidgetHLayout.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	RectWidgetVLayout: RectWidgetVLayout.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	PushButtonWidget: PushButtonWidget.StyleSheet(
		backgroundColor=Blue, roundCornerRadius=20, margin=0, pressColor=(0x8e, 0x8e, 0x8f)),
	ToggleButtonWidget: ToggleButtonWidget.StyleSheet(
		backgroundColor=Blue, roundCornerRadius=20, margin=0, pressColor=(0x8e, 0x8e, 0x8f)),
	IconedPushButtonWidget: IconedPushButtonWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
		roundCornerRadius=10, margin=10, iconMargin=5),
	LabeledPushButtonWidget: LabeledPushButtonWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f), pressColor=(0x8e, 0x8e, 0x8f),
		roundCornerRadius=10, margin=10, textMargin=5),
	ToggleWidget: ToggleWidget.StyleSheet(
		onColor=(0x23, 0x24, 0x25), offColor=LightGray, nodeColor=White, nodePadding=4, margin=4),
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
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56), roundCornerRadius=0, margin=0),
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

	RectWidgetHolder: RectWidgetHolder.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0),
	
	CanvasWidget: CanvasWidget.StyleSheet(
		backgroundColor=(0x2e, 0x2e, 0x2f), hoverColor=(0x2e, 0x2e, 0x2f),
		roundCornerRadius=0, margin=0),
	SidebarButtonWidget: SidebarButtonWidget.StyleSheet(
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

	FileExplorerEntry: FileExplorerEntry.StyleSheet(
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x65, 0x66, 0x66), pressColor=(0x85, 0x86, 0x86)),
	FileExplorerExplorer: FileExplorerExplorer.StyleSheet(
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x45, 0x46, 0x46)),
	FileExplorerWidgetContent: FileExplorerWidgetContent.StyleSheet(),

	StampLibraryEntry: StampLibraryEntry.StyleSheet(
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x65, 0x66, 0x66), pressColor=(0x85, 0x86, 0x86)),
	StampLibraryLineEntry: StampLibraryLineEntry.StyleSheet(),
	StampLibraryExplorer: StampLibraryExplorer.StyleSheet(
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x45, 0x46, 0x46)),
	StampLibraryWidgetContent: StampLibraryWidgetContent.StyleSheet(),

	ApplicationWidget: ApplicationWidget.StyleSheet()
}