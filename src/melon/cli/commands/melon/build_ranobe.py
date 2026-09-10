from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableTypes

from ....builders.ranobe import RanobeBuilder
from ....core import exceptions
from ....core.base.formats.base_format.enums import By
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	filename: str
	branch_id: int | None

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

		position = model.create_position("FILE", "Filename of local JSON.", important = True)
		position.set_argument()

		self._add_parser_position(key = "--use")

		model.base.add_key("--branch", value_type = ValidableTypes.UnsignedInteger, description = "Branch ID to building.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Build read-ready ranobe content."

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
			filename = entity.get_position_value("FILE", expected_type = str, important = True),
			required_parser = prepared_data.required_parsers[0],
			branch_id = entity.get_key_value("--branch", expected_type = int)
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
		typing_result = source_operator.get_content_type_by_file(parameters.filename)

		typing_result = source_operator.get_content_type_by_file(parameters.filename)

		if not typing_result.slug:
			raise exceptions.builders.BuildingError("Undefined title slug.")

		Parser = source_operator.launch_parser(typing_result.content_type)
		
		Title = Parser.init_empty_title(typing_result.slug)
	
		if Title.load(parameters.filename, By.Filename):
			self.printer.emit(f"Loaded file: <i>{parameters.filename}</i>.")
		else:
			self.printer.error(f"Unable load file: <b>{parameters.filename}</b>.")
			return False
	
		Builder = RanobeBuilder(Parser, Title)
		Builder.build(parameters.branch_id)

		return True