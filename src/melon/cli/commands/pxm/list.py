from typing import TYPE_CHECKING, override

from ....core.base.parsers.components.manifest import ContentTypes
from ...base import BaseCommandProcessor
from ...base.structs import ProcessorOptions
from ...base.templates import BaseParameters

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

class CommandProcessor(BaseCommandProcessor[BaseParameters]):
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

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "List installed parsers."

	@override
	def _export_options(self) -> ProcessorOptions:
		"""
		Возвращает настройки обработчика.

		:return: Настройки обработчика.
		:rtype: ProcessorOptions
		"""

		return ProcessorOptions(use_timer = False)

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> BaseParameters:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: BaseParameters
		"""

		return BaseParameters()

	@override
	def _process(self, parameters: BaseParameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Параметры, требуемые обработчиком.
		:type parameters: BaseParameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		TableData: dict[str, list[str]] = {
			"NAME": [],
			"VERSION": [],
			"TYPES": [],
			"DOMAIN": [],
			"collect": []
		}
	
		for ParserName in self.system_objects.manager.parsers.installed:
			SourceOperator = self.system_objects.manager.parsers.get_operator(ParserName).launch()
			TypesEmoji = {
				ContentTypes.Manga: "m",
				ContentTypes.Ranobe: "r"
			}
	
			ParserVersion = SourceOperator.parser_version or ""
			ParserContentTypes: list[str] = [TypesEmoji[CurrentType] for CurrentType in SourceOperator.manifest.content_types]
			ParserSite: str = "https://" + SourceOperator.manifest.domain
	
			TableData["NAME"].append(ParserName)
			TableData["VERSION"].append(ParserVersion)
			TableData["TYPES"].append(", ".join(ParserContentTypes))
			TableData["DOMAIN"].append(ParserSite)
			TableData["collect"].append(str(SourceOperator.is_collector_implemented))
	
		self.printer.templates.manager.parsers_table(TableData)

		return True
