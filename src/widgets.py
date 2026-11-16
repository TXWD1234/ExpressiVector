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

@dataclass(slots=True)
class IconedPushButtonWidget(PushButtonWidget):
	# ================ Contract Interface ================

	def __post_init__(self):
		self.setOverlay(IconOverlay)

	def activateLayout(self):
		self.overlay.styleSheet.margin = self.styleSheet.iconMargin + self.styleSheet.margin
		self.overlay.setImage(pygame.transform.scale(
			self.source, scaleToFit(
				ivec2.fromTuple(self.source.get_size()),
			    self.dim - ivec2(self.overlay.styleSheet.margin,
			                     self.overlay.styleSheet.margin) * 2).toTuple()))

	# ================ Public Interface ================

	source: pygame.Surface | None = None

	# ================ Style ================

	@dataclass(slots=True)
	class StyleSheet(PushButtonWidget.StyleSheet):
		iconMargin: int = 0
	styleSheet: StyleSheet = field(default_factory=StyleSheet)

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
	proportion: InitVar[tuple[int, int] | None ] = None

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

@dataclass(slots=True)
class ColorPickerWidget(RectWidgetBase):
	pass

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
	content: ConfigSectionContent = section.content

# ================ Stroke ================

def configSectionStrokeSize(section: ConfigSection):
	sectionAdd(section, text="Width", entryWidgetType=SliderHWidget, entryWidgetArgs={})
	sectionAdd(section, text="Height", entryWidgetType=IntegerLineEditWidget, entryWidgetArgs={"scope": (0, 100)}, proportion=(1, 2))
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
		section = self.configWidget.addWidget(UnitedLinearLayoutAttribute(), ConfigSection, name="Geometry")
		configSectionStrokeSize(section)

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
		backgroundColor=Blue, roundCornerRadius=20, margin=10),
	ToggleWidget: ToggleWidget.StyleSheet(
		onColor=Blue, offColor=LightGray, nodeColor=White, nodePadding=4),
	DragWidget: DragWidget.StyleSheet(
		backgroundColor=Blue, roundCornerRadius=20, margin=10),
	SliderHWidget: SliderWidgetBase.StyleSheet(
		backgroundColor=(0xae, 0xae, 0xaf), backgroundEmptyColor=(0x55, 0x56, 0x56), hoverColor=(0xce, 0xce, 0xcf),
		draggerNormalColor=(0x7e, 0x7e, 0x7f), draggerHoverColor=(0x5e, 0x5e, 0x5f), draggerDragColor=(0x3f, 0x3f, 0x3f),
		draggerMargin=-5, roundCornerRadius=20, margin=10),
	SliderVWidget: SliderWidgetBase.StyleSheet(
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
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x35, 0x36, 0x36), editColor=(0x15, 0x16, 0x16),
		borderWidth=1, borderColor=(0x7e, 0x7e, 0x7f), hoverBorderColor=(0xae, 0xae, 0xaf),
		roundCornerRadius=4, margin=4,
		textIndentation=10, textColor=White,
		cursorColor=White, cursorWidth=2),
	IntegerLineEditWidget: IntegerLineEditWidget.StyleSheet(
		backgroundColor=(0x45, 0x46, 0x46), hoverColor=(0x35, 0x36, 0x36), editColor=(0x15, 0x16, 0x16),
		borderWidth=1, borderColor=(0x7e, 0x7e, 0x7f), hoverBorderColor=(0xae, 0xae, 0xaf),
		roundCornerRadius=4, margin=4,
		textIndentation=10, textColor=White,
		cursorColor=White, cursorWidth=2),

	CanvasWidget: CanvasWidget.StyleSheet(
		backgroundColor=(0x2e, 0x2e, 0x2f), hoverColor=(0x2e, 0x2e, 0x2f),
		roundCornerRadius=0, margin=0),
	IconedPushButtonWidget: IconedPushButtonWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f),
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
	ApplicationWidget: ApplicationWidget.StyleSheet()
}