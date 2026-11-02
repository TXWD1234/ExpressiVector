import math
from dataclasses import dataclass

def dot(in1: 'vec2', in2: 'vec2') -> float:
	return in1.x * in2.x + in1.y * in2.y

@dataclass(slots=True)
class vec2:
	x: float
	y: float
	
	def __init__(self, x: float = 0.0, y: float = 0.0):
		self.x = x
		self.y = y

	def set(self, in_x: float, in_y: float):
		self.x = float(in_x)
		self.y = float(in_y)

	def setX(self, in_x: float): self.x = float(in_x)
	def setY(self, in_y: float): self.y = float(in_y)
	
	def getX(self) -> float: return self.x
	def x(self) -> float: return self.x
	def getY(self) -> float: return self.y
	def y(self) -> float: return self.y

	def __add__(self, other):
		if isinstance(other, vec2):
			return vec2(self.x + other.x, self.y + other.y)
		return vec2(self.x + other, self.y + other)

	def __sub__(self, other):
		if isinstance(other, vec2):
			return vec2(self.x - other.x, self.y - other.y)
		return vec2(self.x - other, self.y - other)

	def __mul__(self, coef: float):
		return vec2(self.x * coef, self.y * coef)

	def __rmul__(self, coef: float):
		return vec2(self.x * coef, self.y * coef)

	def __truediv__(self, coef: float):
		return vec2(self.x / coef, self.y / coef)
		
	def __rtruediv__(self, coef: float):
		return vec2(self.x / coef, self.y / coef)

	def __iadd__(self, other):
		if isinstance(other, vec2):
			self.x += other.x
			self.y += other.y
		else:
			self.x += other
			self.y += other
		return self

	def __isub__(self, other):
		if isinstance(other, vec2):
			self.x -= other.x
			self.y -= other.y
		else:
			self.x -= other
			self.y -= other
		return self

	def __imul__(self, coef: float):
		self.x *= coef
		self.y *= coef
		return self

	def __eq__(self, other):
		if not isinstance(other, vec2): return False
		# Python's built-in float comparison with a default epsilon
		return math.isclose(self.x, other.x, abs_tol=1e-5) and math.isclose(self.y, other.y, abs_tol=1e-5)

	def __ne__(self, other):
		return not self.__eq__(other)

	def __lt__(self, other):
		return (self.x**2 + self.y**2) < (other.m_x**2 + other.m_y**2)

	def __gt__(self, other):
		return (self.x**2 + self.y**2) > (other.m_x**2 + other.m_y**2)

	def length(self) -> float:
		return math.sqrt(dot(self, self))

	def offset(self, x: float, y: float) -> 'vec2':
		return self + vec2(x, y)

	def offsetX(self, in_x: float) -> 'vec2':
		return vec2(self.x + in_x, self.y)

	def offsetY(self, in_y: float) -> 'vec2':
		return vec2(self.x, self.y + in_y)

	def __str__(self):
		return f"( {self.x}, {self.y} )"

@dataclass(slots=True)
class ivec2:
	x: int
	y: int
	
	def __init__(self, x: int = 0, y: int = None):
		self.x = int(x)
		self.y = int(x if y is None else y)

	def set(self, in_x: int, in_y: int):
		self.x = int(in_x)
		self.y = int(in_y)

	def setX(self, in_x: int): self.x = int(in_x)
	def setY(self, in_y: int): self.y = int(in_y)
	
	def getX(self) -> int: return self.x
	def x(self) -> int: return self.x
	def getY(self) -> int: return self.y
	def y(self) -> int: return self.y

	def __add__(self, other: 'ivec2'):
		return ivec2(self.x + other.x, self.y + other.y)

	def __sub__(self, other: 'ivec2'):
		return ivec2(self.x - other.x, self.y - other.y)

	def __iadd__(self, other: 'ivec2'):
		self.x += other.x
		self.y += other.y
		return self

	def __isub__(self, other: 'ivec2'):
		self.x -= other.x
		self.y -= other.y
		return self

	def __eq__(self, other):
		if not isinstance(other, ivec2): return False
		return self.x == other.x and self.y == other.y

	def __ne__(self, other):
		return not self.__eq__(other)

	def __lt__(self, other: 'ivec2'):
		return (self.x**2 + self.y**2) < (other.x**2 + other.y**2)

	def __gt__(self, other: 'ivec2'):
		return (self.x**2 + self.y**2) > (other.x**2 + other.y**2)

	def __mul__(self, in_val: float) -> vec2:
		return vec2(self.x * in_val, self.y * in_val)

	def valid(self, edge: int) -> bool:
		return 0 <= self.x < edge and 0 <= self.y < edge

	def offset(self, in_x: int, in_y: int) -> 'ivec2':
		return ivec2(self.x + in_x, self.y + in_y)

	def offsetX(self, in_x: int) -> 'ivec2':
		return ivec2(self.x + in_x, self.y)

	def offsetY(self, in_y: int) -> 'ivec2':
		return ivec2(self.x, self.y + in_y)

	def move(self, in_x: int, in_y: int):
		self.x += in_x
		self.y += in_y

	def moveX(self, in_x: int):
		self.x += in_x

	def moveY(self, in_y: int):
		self.y += in_y

	def __str__(self):
		return f"( {self.x}, {self.y} )"


def toIvec2(in_vec: vec2) -> ivec2:
	return ivec2(math.floor(in_vec.x()), math.floor(in_vec.y()))

def toVec2(in_coord: ivec2) -> vec2:
	return vec2(float(in_coord.x()), float(in_coord.y()))

@dataclass(slots=True)
class Rect:
	topLeft: ivec2
	diagnal: ivec2
	
	def __init__(self, topLeft: ivec2, width: int, height: int):
		self.topLeft = topLeft
		self.diagnal = ivec2(width, height)

	def toPygameRect(self):
		return (self.topLeft.x)