from typing import TYPE_CHECKING, override

from prettytable import PLAIN_COLUMNS, PrettyTable

from dublib.cli.text_styler import FastStyler

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

		return "Show list of repositories."

	def _export_options(self) -> ProcessorOptions:
		"""
		Возвращает настройки обработчика.

		:return: Настройки обработчика.
		:rtype: ProcessorOptions
		"""

		return ProcessorOptions(use_timer = False)

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: PreparedData) -> BaseParameters:
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

		:param parameters: Требуемые параметры.
		:type parameters: BaseParameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		InstalledParsers: list[str] = self.system_objects.manager.parsers.installed

		TableData: dict[str, list[str]] = {
			"PARSER": [],
			"REPOSITORY": []
		}
	
		for ParserName in self.system_objects.manager.repositories.availabel_parsers:
			RepositoryURL: str = self.system_objects.manager.repositories.get(ParserName, exception = True)
			Status = "✅" if ParserName in InstalledParsers else "❌"
			TableData["PARSER"].append(f"{Status} {ParserName}")
			TableData["REPOSITORY"].append(FastStyler(RepositoryURL).decorate.italic)

		TableObject = PrettyTable()
		TableObject.set_style(PLAIN_COLUMNS)

		for ColumnName in TableData.keys():
			Buffer = FastStyler(ColumnName).decorate.bold
			TableObject.add_column(Buffer, TableData[ColumnName])

		TableObject.align = "l"
		TableObject.sortby = FastStyler("PARSER").decorate.bold
		TableString = str(TableObject).strip()
		self.printer.emit(TableString)

		return True
