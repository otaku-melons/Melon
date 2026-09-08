from typing import TYPE_CHECKING

from dublib.cli.text_styler import FastStyler

from ._base import _BaseTemplatesSection

if TYPE_CHECKING:
	from .....utils.classificator.structs import ClassificationResult

class ClassificatorTemplates(_BaseTemplatesSection):
	"""Расширенные шаблоны вывода: оператор обработки классификаторов."""

	def result(self, result: "ClassificationResult"):
		"""
		Шаблон вывода: оператор обработки классификаторов.

		:param result: Результат обработки классификатора.
		:type result: ClassificationResult
		"""

		if not result.is_operation_found:
			self.printer.error("Operation not found.")
			return
		
		if result.delete:
			self.printer.emit("Classificator must be deleted.")
			return

		self.printer.emit(f"Name: <i>{result.name}</i>")
		is_renamed: str = str(result.is_renamed).lower()
		self.printer.emit(f"Renamed: {is_renamed}")
		classificator_type :str = result.type.name.lower() if result.type else FastStyler("null").colorize.red
		self.printer.emit(f"Type: {classificator_type}")
