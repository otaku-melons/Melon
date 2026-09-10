from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from dublib.cli.text_styler import FastStyler
from dublib.validators import ValidableTypes

from ....core.base.structs.title import TitleDescriptor
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	slug: str | None
	title_id: int | None
	is_json_output: bool

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __print_result(self, parameters: Parameters, descriptor: TitleDescriptor):
		"""
		Выводит результат поиска ID.

		:param parameters: Параметры команды.
		:type parameters: Parameters
		:param descriptor: Дескриптор тайтла.
		:type descriptor: TitleDescriptor
		"""

		file_path: str | None = None

		if descriptor.path and descriptor.path.exists():
			file_path = descriptor.path.as_posix()

		if parameters.is_json_output:
			OutputDictionary: dict[str, int | str | None] = {
				"parser": parameters.required_parser.name,
				"slug": descriptor.slug,
				"id": descriptor.id,
				"path": file_path
			}
			self.printer.json(OutputDictionary)

		else:
			data: dict[str, int | str | None] = {
				"Parser": parameters.required_parser.name,
				"Slug": descriptor.slug,
				"ID": descriptor.id,
				"Path": file_path
			}

			if not file_path:
				del data["Path"]

			for key, value in data.items():
				value = FastStyler(str(value)).decorate.italic if value else FastStyler("not found").colorize.red
				self.printer.emit(f"{key}: {value}")

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

		position = model.create_position("QUERY", "Seqrch query", important = True)
		position.add_key("--id", value_type = ValidableTypes.UnsignedInteger, description = "Title ID.")
		position.set_argument(description = "Title slug.")

		self._add_parser_position(key = "--use")
		self._add_json_output_flag()

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Find title identificator in cache."

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

		title_id: int | None = entity.get_key_value("--id", expected_type = int, not_found_error = False)
		slug: str | None = None

		if not title_id:
			slug = entity.get_position_value("QUERY", expected_type = str, important = True)

		return Parameters(
			required_parser = prepared_data.required_parsers[0],
			is_json_output = prepared_data.is_json_output,
			slug = slug,
			title_id = title_id
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

		if not self.system_objects.options.USE_CACHE:
			self.printer.error("Cache using disabled. Unprocessable.")
			return False

		source_operator = self._launch_source_operator(parameters.required_parser)
		descriptor = TitleDescriptor(source_operator)

		if parameters.title_id:
			descriptor.set_id(parameters.title_id)
			slug: str | None = source_operator.shared_data.journal.get_slug_by_id(parameters.title_id)
			if slug: descriptor.set_slug(slug)

		elif parameters.slug:
			descriptor.set_slug(parameters.slug)
			title_id: int | None = source_operator.shared_data.journal.get_id_by_slug(parameters.slug)
			if title_id: descriptor.set_id(title_id)

		self.__print_result(parameters, descriptor)

		return True
