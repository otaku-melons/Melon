from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableTypes

from ....utils.cutter import Cutter
from ...base.templates import BaseParameters
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(BaseParameters):
	"""Параметры, требуемые обработчиком."""

	image: Path
	templates: Path
	output: Path | None
	is_dry: bool

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __get_templates(self, parameters: Parameters, cutter: Cutter) -> tuple[Path, ...]:
		"""
		Получает шаблоны.

		:param parameters: Параметры, требуемые обработчиком.
		:type parameters: Parameters
		:param cutter: Инструмент для вырезания рекламы из слайдов манги.
		:type cutter: Cutter
		:return: Последовательность путей к шаблонам.
		:rtype: tuple[Path, ...]
		"""
		
		templates: tuple[Path, ...] = (parameters.templates, )

		if parameters.templates.is_dir():
			templates = cutter.get_templates_from_directory(parameters.templates)

		self.printer.emit(f"Templates loaded: {len(templates)}.")

		return templates

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Генерирует модель команды.
		
		:param model: Шаблон модели команды.
		:type model: Command
		:return: Модель команды.
		:rtype: CommandModel
		"""

		position = model.create_position("IMAGE", "Path to image.", important = True)
		position.set_argument(ValidableTypes.ValidPath)

		position = model.create_position("TEMPLATES", "Templates source.", important = True)
		position.add_key("--dir", value_type = ValidableTypes.ValidPath, description = "Path to templates images directory.")
		position.set_argument(value_type = ValidableTypes.ValidPath, description = "Path to template image.")

		position = model.create_position("OUTPUT", "Output image path.")
		position.set_argument(ValidableTypes.Path)

		model.base.add_flag("-d", description = "Dry run for only matches checking.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Cut full-width templates from image."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> Parameters:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: Parameters
		"""
		
		return Parameters(
			image = entity.get_position_value("IMAGE", expected_type = Path, important = True),
			templates = entity.get_position_value("TEMPLATES", expected_type = Path, important = True),
			output = entity.get_position_value("OUTPUT", expected_type = Path, important = False),
			is_dry = entity.check_flag("-d")
		)

	@override
	def _process(self, parameters: Parameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Параметры, требуемые обработчиком.
		:type parameters: Parameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		cutter = Cutter(self.system_objects)
		templates: tuple[Path, ...] = self.__get_templates(parameters, cutter)

		if not templates:
			return True

		if parameters.is_dry:
			matches: int = cutter.calculate_templates_matches(parameters.image, templates)
			self.printer.emit(f"Matches found: {matches}.")
			return True
		
		cutted_templates_count: int = cutter.clean_image(parameters.image, templates, parameters.output)

		if cutted_templates_count:
			self.printer.emit(f"Cutted {cutted_templates_count} templates from image.")

			if parameters.output: self.printer.emit(f"Image path: <i>{parameters.output}</i>")
			else: self.printer.emit("Original image overwritten.")

		else:
			self.printer.emit("No templates matches for image.")

		return True
