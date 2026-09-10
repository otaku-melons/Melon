from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableTypes

from ...base.templates import T_ForceModeRequired, T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_ForceModeRequired, T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	link: str
	directory: Path | None
	full_name: str | None
	name: str | None

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Обработчик команды."""

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

		position = model.create_position("URL", "Link to image.", important = True)
		position.set_argument(ValidableTypes.URL)

		self._add_parser_position(key = "--use")

		position = model.create_position("NAME", "Naming operation. By default save original.")
		position.add_key("--fullname", description = "Set full name with file extension.")
		position.add_key("--name", description = "Rename, but save original file extension.")

		self._add_force_mode_flag()

		model.base.add_key("--dir", value_type = ValidableTypes.ValidPath, description = "Output directory.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Download image by URL."

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
			required_parser = prepared_data.required_parsers[0],
			force_mode = prepared_data.force_mode,
			link = entity.get_position_value("URL", expected_type = str, important = True),
			directory = entity.get_key_value("--dir", expected_type = Path),
			full_name = entity.get_key_value("--fullname", expected_type = str),
			name = entity.get_key_value("--name", expected_type = str)
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

		source_operator = self._launch_source_operator(parameters.required_parser)
		filename: str = source_operator.images_downloader.build_target_filename(
			url = parameters.link,
			filename = parameters.full_name or parameters.name,
			is_full_filename = bool(parameters.full_name),
		)

		Future = self.printer.templates.images.start_downloading(filename)

		result = source_operator.download_image(
			url = parameters.link,
			directory = parameters.directory,
			filename = parameters.full_name or parameters.name,
			is_full_filename = bool(parameters.full_name),
			force_mode = parameters.force_mode
		)
	
		Future.result(result, show_path = True)

		return True
