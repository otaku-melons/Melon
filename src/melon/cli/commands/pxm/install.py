from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ....core.system_objects.manager.parsers import ExportStrategies
	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	config_strategy: ExportStrategies

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

		self._add_parser_position()
		self._add_settings_export_strategy_position()

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Install parser."

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

		strategy: str | None = entity.get_position_value("STRATEGY", expected_type = str)
		if not strategy: strategy = "-s"

		return Parameters(
			required_parser = prepared_data.required_parsers[0],
			config_strategy = ExportStrategies(strategy)
		)

	@override
	def _process(self, parameters: Parameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Требуемые параметры.
		:type parameters: Parameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		repository_url: str = self.system_objects.manager.repositories.get(parameters.required_parser.name, exception = True)

		self.printer.emit(f"Repository: <i>{repository_url}</i>.")
		parameters.required_parser.install()
		self.printer.emit("Parser installed.")

		self.system_objects.manager.packager.install_requirements(parameters.required_parser.requirements_path)

		result = parameters.required_parser.export_settings(parameters.config_strategy)
		self.printer.templates.manager.exported(result)

		return True
