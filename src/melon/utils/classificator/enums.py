from dataclasses import dataclass
from enum import Enum

class Cases(Enum):
	"""Перечисление приведений регистра."""

	Low = "low"
	Up = "up"
	Title = "title"

class ClassificatorsTypes(Enum):
	"""Перечисление типов классификаторов."""

	Franchise = "franchises"
	Genre = "genres"
	Person = "persons"
	Tag = "tags"

@dataclass(frozen = True)
class _DirectiveValidationData:
	"""
	Данные валидации директивы.
	
	* **values** – последовательность принимаемых значений или `None` для любого значения;
	* **allow_list** – разрешено ли указание нескольких значений;
	* **allow_empty** – разрешено ли не указывать значения.
	"""

	values: tuple[str, ...] | None
	allow_list: bool
	allow_empty: bool

class Directives(Enum):
	"""Перечисление директив."""
	
	DELETE = _DirectiveValidationData(values = None, allow_list = False, allow_empty = True)
	DROP = _DirectiveValidationData(values = ("case", "delete", "type"), allow_list = True, allow_empty = True)
	CASE = _DirectiveValidationData(values = ("low", "title", "up"), allow_list = False, allow_empty = True)
	INCLUDE = _DirectiveValidationData(values = None, allow_list = False, allow_empty = False)
	TYPE = _DirectiveValidationData(values = ("franchises", "genres", "persons", "tags"), allow_list = False, allow_empty = False)