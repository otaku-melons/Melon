from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ....utils.collector import Collector
from ...base.templates import T_SingleParserRequired
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	origin: str
	target: str
	clear_origin: bool

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

		position = model.create_position("ORIGIN", "Processed collection name.", important = True)
		position.set_argument()

		position = model.create_position("TARGET", "Result collection name.", important = True)
		position.set_argument()

		self._add_parser_position(key = "--use")

		model.base.add_flag("-c", description = "Remove origin file.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Merge slugs collections."

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
			origin = entity.get_position_value("ORIGIN", expected_type = str, important = True),
			target = entity.get_position_value("TARGET", expected_type = str, important = True),
			clear_origin = entity.check_flag("-c")
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

		origin_collector = Collector(source_operator, parameters.origin)
		origin_collector.load()
		target_collector = Collector(source_operator, parameters.target)
		target_collector.load()

		unique_slugs_added: int = target_collector.add(origin_collector.slugs)
		self.printer.emit(f"From <b>{parameters.origin}</b> added {unique_slugs_added} unique slugs to <b>{parameters.target}</b> collection.")

		if parameters.clear_origin:
			origin_collector.clear()
			self.printer.emit("Origin file deleted.")

		return True
