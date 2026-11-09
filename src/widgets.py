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

# ################ Side Bar ################

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

@dataclass(slots=True)
class ConfigWidgetOutline(RectWidgetBase):
	pass


# ################ Application ################

@dataclass(slots=True, weakref_slot=True)
class ApplicationWidget(RectWidgetHLayout):
	def __post_init__(self):
		self.addWidget(LinearLayoutAttribute(order=0), CanvasWidget)
		self.addWidget(LinearLayoutAttribute(order=1, absolute=True, visible=False, proportion=0.2), ConfigWidgetOutline)
		self.addWidget(LinearLayoutAttribute(order=2, absolute=True, proportion=0.04), SidebarWidget)

	# Contrainted Contract Interface
	# Will be called everytime with updated uniform state
	def editStateUpdate(self):
		if (self.uniform.editState == EditState.Nothing): self.widgets[1].hide()
		else: self.widgets[1].show()
		


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
		backgroundColor=MikuColorBegin, hoverColor=White,
		draggerNormalColor=LightBlue, draggerHoverColor=Red, draggerDragColor=Blue,
		draggerMargin=4, roundCornerRadius=20, margin=10),
	SliderVWidget: SliderWidgetBase.StyleSheet(
		backgroundColor=MikuColorBegin, hoverColor=White,
		draggerNormalColor=LightBlue, draggerHoverColor=Red, draggerDragColor=Blue,
		draggerMargin=4, roundCornerRadius=20, margin=10),
	LabelOverlay: LabelOverlay.StyleSheet(
		margin=10, textColor=White, fontSize=64),
	LabelWidget: LabelWidget.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),
	IconOverlay: IconOverlay.StyleSheet(
		margin=0),
	IconWidget: IconWidget.StyleSheet(
		backgroundColor=MikuColorBegin, roundCornerRadius=20, margin=0),

	CanvasWidget: CanvasWidget.StyleSheet(
		backgroundColor=(0x2e, 0x2e, 0x2f), hoverColor=(0x2e, 0x2e, 0x2f),
		roundCornerRadius=0, margin=0),
	IconedPushButtonWidget: IconedPushButtonWidget.StyleSheet(
		backgroundColor=(0x53, 0x54, 0x55), hoverColor=(0x6e, 0x6e, 0x6f),
		roundCornerRadius=10, margin=10, iconMargin=5),
	SidebarWidget: SidebarWidget.StyleSheet(
		backgroundColor=(0x47, 0x47, 0x47), hoverColor=(0x47, 0x47, 0x47),
		roundCornerRadius=0, margin=0),
	ConfigWidgetOutline: ConfigWidgetOutline.StyleSheet(
		backgroundColor=(0x55, 0x56, 0x56), hoverColor=(0x55, 0x56, 0x56),
		roundCornerRadius=0, margin=0),
	ApplicationWidget: ApplicationWidget.StyleSheet()
}