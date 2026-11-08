# Copyright (c) 2026 ExpressiVector. Licensed under the MIT License.

from .widget_infrastructure import *
from .canvas_widget import *

# ============================================================================
# **************** Application Specific Widget Implementation ****************
# ============================================================================

# ################ Side Bar ################

@dataclass(slots=True)
class ApplicationWidget(RectWidgetHLayout):
	pass