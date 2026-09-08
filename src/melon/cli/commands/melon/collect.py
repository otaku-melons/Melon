from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, override

from dublib.cli.text_styler import get_styled_text_from_html
from dublib.validators import ValidableTypes

from .... import utils
from ...base.templates import T_ForceModeRequired, T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class CollectingTargets(Enum):
	"""Альтернативный цели для сборки коллекции."""

	FromServer = None
	Local = "-local"
	NotFound = "-not-found"

@dataclass(frozen = True)
class Parameters(T_ForceModeRequired, T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	file: str | None
	collecting_target: CollectingTargets

	period: int | None
	filters: str | None
	pages: int | None

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __collect_from_source(self, collector: utils.Collector, parameters: Parameters) -> int:
		"""
		Собирает алиасы тайтлов: с сервера источника по заданным параметрам.

		:param collector: Сборщик алиасов.
		:type collector: utils.Collector
		:param parameters: Параметры, требуемые обработчиком.
		:type parameters: Parameters
		:return: Количество уникальных добавленных в коллекцию тайтлов.
		:rtype: int
		"""

		source_operator = self._launch_source_operator(parameters.required_parser)
		slugs = source_operator.collect_slugs(parameters.period, parameters.filters, parameters.pages)

		return collector.add(slugs)

	def __collect_local(self, collector: utils.Collector) -> int:
		"""
		Собирает алиасы тайтлов: локальные файлы.

		:param collector: Сборщик алиасов.
		:type collector: utils.Collector
		:return: Количество уникальных добавленных в коллекцию тайтлов.
		:rtype: int
		"""

		self.printer.templates.collector.start()

		return collector.collect_local().added

	def __collect_not_found(self, collector: utils.Collector) -> int:
		"""
		Собирает алиасы тайтлов: не найденные на сервере источника тайтлы.

		:param collector: Сборщик алиасов.
		:type collector: utils.Collector
		:return: Количество уникальных добавленных в коллекцию тайтлов.
		:rtype: int
		"""

		self.printer.emit("Checking titles existing…", flush = True)

		if collector.is_operation_cached:
			self.printer.debug("Using previous operation cache.")

		return collector.collect_not_found().added

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

		self._add_parser_position(key = "--use")

		position = model.create_position("TARGETS", "Alternative targets to collecting.")
		position.add_flag(CollectingTargets.Local.value, description = "Scan local titles and put slugs into collection.")
		position.add_flag(CollectingTargets.NotFound.value, description = "Check titles existing on server and collect not found slugs.")

		position = model.create_position(
			name = "FILE",
			description = get_styled_text_from_html("Collection filename without filetype. By default <i>collection</i>.")
		)
		position.add_key("--file")

		self._add_force_mode_flag()
		self._add_mirror_key()

		model.base.add_key("--filters", description = "Query string for filtering titles.")
		model.base.add_key("--pages", value_type = ValidableTypes.UnsignedInteger, description = "Count of pages to collecting.")
		model.base.add_key("--period", value_type = ValidableTypes.UnsignedInteger, description = "Period in hours for parsing updates.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Collect titles slugs into file in parser's temporary directory."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: PreparedData) -> Parameters:
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
			file = entity.get_position_value("FILE", expected_type = str),
			collecting_target = CollectingTargets(entity.get_position_value("TARGETS", expected_type = str)),
			period = entity.get_key_value("--period", expected_type = int),
			filters = entity.get_key_value("--filters", expected_type = str),
			pages = entity.get_key_value("--pages", expected_type = int)
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

		source_operator = self._launch_source_operator(parameters.required_parser)
		collector = utils.Collector(source_operator, parameters.file)

		if not parameters.force_mode:
			collector.load()

		added_slugs_count: int = 0

		match parameters.collecting_target:

			case CollectingTargets.FromServer:

				if not source_operator.is_collector_implemented:
					self.printer.critical("Collector method not implemented.")
					return False

				added_slugs_count = self.__collect_from_source(collector, parameters)

			case CollectingTargets.Local: added_slugs_count = self.__collect_local(collector)
			case CollectingTargets.NotFound: added_slugs_count = self.__collect_not_found(collector)

		collector.save()
	
		if added_slugs_count: self.printer.emit(f"Unique slugs added: {added_slugs_count}.")
		else: self.printer.emit("No new slugs in collection.")

		return True
