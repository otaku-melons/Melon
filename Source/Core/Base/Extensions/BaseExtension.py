from Source.Core.Base.Parsers.Components.Settings import ParserSettings
from Source.Core.SystemObjects.Logger import Portals
from Source.Core.SystemObjects import SystemObjects

from dublib.CLI.Terminalyzer import Command, ParsedCommandData, Terminalyzer
from dublib.WebRequestor import Protocols, WebConfig, WebLibs, WebRequestor
from dublib.Engine.Bus import ExecutionStatus

from typing import TYPE_CHECKING
import shlex

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.BaseParser import BaseParser

#==========================================================================================#
# >>>>> ОПРЕДЕЛЕНИЯ <<<<< #
#==========================================================================================#

VERSION = None
NAME = None

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class BaseExtension:
	"""Базовое расширение."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def force_mode(self) -> bool:
		"""Состояние: включён ли глобальный режим перезаписи."""

		return self._SystemObjects.FORCE_MODE.status

	@property
	def parser_settings(self) -> ParserSettings:
		"""Настройки парсера."""

		return self._ParserSettings
	
	@property
	def portals(self) -> Portals:
		"""Настройки парсера."""

		return self._Portals

	@property
	def requestor(self) -> WebRequestor:
		"""Запросчик Web-контента."""

		return self._Requestor
	
	@property
	def settings(self) -> dict | None:
		"""Настройки расширения."""

		return self._Settings
	
	@property
	def system_objects(self) -> SystemObjects:
		"""Коллекция системных объектов."""

		return self._SystemObjects

	@property
	def temp(self) -> str:
		"""Путь к каталогу."""

		return self._Temper.extension_temp

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _GenerateCommandsList(self) -> list[Command]:
		"""Возвращает список описаний команд."""

		CommandsList = list()

		return CommandsList

	def _InitializeRequestor(self) -> WebRequestor | None:
		"""
		Инициализирует оператор WEB-запросов.

		:return: Оператор запросов или `None` для использования стандартного запросчика из парсера.
		:rtype: WebRequestor | None
		"""

		pass

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass

	def _ProcessCommand(self, command: ParsedCommandData):
		"""
		Вызывается для обработки переданной расширению команды.
			command – данные команды.
		"""

		pass

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: SystemObjects, parser: "BaseParser"):
		"""
		Базовое расширение.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param parser: Парсер.
		:type parser: BaseParser
		"""

		self._SystemObjects = system_objects
		self._Parser = parser

		self._Manifest = self._SystemObjects.manager.get_extension_manifest()
		self._ParserManifest = self._Parser.manifest

		self._Temper = self._SystemObjects.temper
		self._Portals = self._SystemObjects.logger.portals
		self._ParserSettings = self._Parser.settings
		self._Settings = self._SystemObjects.manager.current_extension_settings
		self._Requestor = self._Parser.requestor

		BufferedRequestor = self._InitializeRequestor()
		if BufferedRequestor: self._Requestor = BufferedRequestor

		self._PostInitMethod()

	def run(self, command: str | None) -> ExecutionStatus:
		"""
		Запускает расширение.

		:param command: Команда для выполнения расширением или `None` при отсутствии таковой.
		:type command: str | None
		:return: Статус выполнения.
		:rtype: ExecutionStatus
		"""

		Status = ExecutionStatus()

		if command: 
			command = shlex.split(command)
			Analyzer = Terminalyzer(command)
			Analyzer.helper.enable()
			ParsedCommand = Analyzer.check_commands(self._GenerateCommandsList())

			if not ParsedCommand:
				Status.push_error("Unknown command.")
				return Status

			self._ProcessCommand(ParsedCommand)

		else: Status.push_error("No command. Use \"--command\" key.")

		return Status