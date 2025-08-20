from Source.Core.Base.Parsers.Components import ParserSettings, ParserManifest
from Source.Core.Base.Extensions.Components import ExtensionManifest

from dublib.Methods.Filesystem import ReadJSON, ListDir
from dublib.CLI.TextStyler.FastStyler import FastStyler

from typing import TYPE_CHECKING
import importlib

if TYPE_CHECKING:
	from Source.Core.Base.Extensions.BaseExtension import BaseExtension
	from Source.Core.Base.Parsers.RanobeParser import RanobeParser
	from Source.Core.Base.Parsers.MangaParser import MangaParser
	from Source.Core.SystemObjects import SystemObjects
	
class Manager:
	"""Менеджер парсеров и расширений."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def parsers_names(self) -> tuple[str]:
		"""Последовательность названий всех доступных парсеров."""

		Parsers = ListDir("Parsers")
		if "Templates" in Parsers: Parsers.remove("Templates")

		return Parsers

	@property
	def current_extension_settings(self) -> dict | None:
		"""Настройки используемого расширения."""

		return self.get_extension_settings(cache = True)

	@property
	def current_parser_settings(self) -> ParserSettings:
		"""Настройки используемого парсера."""

		return self.get_parser_settings(cache = True)

	@property
	def current_parser_manifest(self) -> ParserManifest:
		"""Манифест используемого парсера."""

		return self.get_parser_manifest()

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CheckParser(self, parser: str | None) -> str:
		"""
		Проверяет наличие модуля парсера в системе.

		:param parser: Имя парсера. По умолчанию будет проверен последний использованный парсер.
		:type parser: str | None
		:return: Имя парсера.
		:rtype: str
		"""

		if not parser: parser = self.__Parser

		if parser != None and parser not in self.parsers_names:
			self.__SystemObjects.logger.critical(f"No parser \"{parser}\".")
			print(f"No parser: \"{parser}\".")
			exit(-1)

		return parser

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Менеджер парсеров и расширений.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__SystemObjects = system_objects

		self.__ExtensionManifest = None
		self.__ExtensionSettings = None
		self.__ParserManifest = None
		self.__ParserSettings = None
		self.__Extension = None
		self.__Parser = None

	def launch_extension(self, parser: str, extension: str) -> "BaseExtension":
		"""
		Запускает расширение.

		:param parser: Имя парсера.
		:type parser: str
		:param extension: Имя расширения.
		:type extension: str
		:return: Объект расширения.
		:rtype: BaseExtension
		"""

		parser = self.__CheckParser(parser)
		Module = importlib.import_module(f"Parsers.{parser}.extensions.{parser}-{extension}.main")
		Parser = self.launch_parser(parser)
		Extension = Module.Extension(self.__SystemObjects, Parser)

		ExtensionName = FastStyler(extension).decorate.bold
		self.__SystemObjects.logger.info(f"Running extension: {ExtensionName}...")

		return Extension

	def launch_parser(self, parser: str | None = None) -> "MangaParser | RanobeParser":
		"""
		Запускает парсер.

		:param parser: Имя парсера. По умолчанию будет запущен последний установленный парсер.
		:type parser: str | None
		:return: Объект парсера.
		:rtype: MangaParser | RanobeParser
		"""

		parser = self.__CheckParser(parser)
		Module = importlib.import_module(f"Parsers.{parser}.main")
		Parser = Module.Parser(self.__SystemObjects)

		ParserName = FastStyler(parser).decorate.bold
		Manifest = self.get_parser_manifest(parser)
		Version = Manifest.version
		if Version: Version = f" (version {Version})"
		else: Version = ""
		Text = f"Parser: {ParserName}{Version}."
		self.__SystemObjects.logger.info(Text)
		
		if all((self.__SystemObjects.MELON_VERSION, Manifest.melon_required_version)) and Manifest.melon_required_version != self.__SystemObjects.MELON_VERSION:
			self.__SystemObjects.logger.warning(f"Melon required version: {Manifest.melon_required_version}.")

		return Parser

	def select_extension(self, extension: str):
		"""
		Задаёт имя используемого расширения.

		:param extension: Имя расширения.
		:type extension: str
		"""

		self.__Extension = extension

	def select_parser(self, parser: str):
		"""
		Задаёт имя используемого парсера.

		:param parser: Имя парсера.
		:type parser: str
		"""

		self.__Parser = parser

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ РАБОТЫ С ПАРСЕРАМИ <<<<< #
	#==========================================================================================#

	def check_method_collect(self, parser: str | None = None) -> bool:
		"""
		Проверяет, доступна ли в парсере имплементация метода *collect()*.

		:param parser: Имя парсера. По умолчанию будет произведена проверка для последнего выбранного парсера.
		:type parser: str | None
		:return: Возвращает `True`, если метод *collect()* имплементирован верно.
		:rtype: bool
		"""
		
		parser = self.__CheckParser(parser)
		Module = importlib.import_module(f"Parsers.{parser}.main")
		Parser = Module.Parser
		IsImplemented = True

		try: Parser.collect
		except AttributeError: IsImplemented = False

		return IsImplemented

	def get_parser_settings(self, parser: str | None = None, cache: bool = True) -> ParserSettings:
		"""
		Возвращает настройки парсера.

		:param parser: Имя парсера. По умолчанию будут получены настройки для последнего выбранного парсера.
		:type parser: str | None
		:param cache: Указывает, можно ли взять объект из кэша или нужно инициализировать его занового.
		:type cache: bool
		:return: Настройки парсера.
		:rtype: ParserSettings
		"""

		parser = self.__CheckParser(parser)
		if cache and self.__ParserSettings and parser == self.__SystemObjects.parser_name: return self.__ParserSettings
		self.__ParserSettings = ParserSettings(parser, self.__SystemObjects.logger)

		return self.__ParserSettings

	def get_parser_manifest(self, parser: str | None = None, cache: bool = True) -> ParserManifest:
		"""
		Возвращает манифест парсера.

		:param parser: Имя парсера. По умолчанию будет получен манифест для последнего выбранного парсера.
		:type parser: str | None
		:param cache: Указывает, можно ли взять объект из кэша или нужно инициализировать его занового.
		:type cache: bool
		:return: Манифест парсера.
		:rtype: ParserManifest
		"""

		parser = self.__CheckParser(parser)
		if cache and self.__ParserManifest and parser == self.__SystemObjects.parser_name: return self.__ParserManifest
		self.__ParserManifest = ParserManifest(self.__SystemObjects, parser)

		return self.__ParserManifest

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ РАБОТЫ С РАСШИРЕНИЯМИ <<<<< #
	#==========================================================================================#

	def get_extension_manifest(self, parser: str | None = None, extension: str | None = None, cache: bool = True) -> ExtensionManifest:
		"""
		Возвращает манифест расширения.

		:param parser: Имя парсера. По умолчанию будет использовано последнее заданное.
		:type parser: str | None
		:param extension: Имя расширения. По умолчанию будет получен манифест для последнего запущенного парсера.
		:type extension: str | None
		:param cache: Указывает, можно ли взять объект из кэша или нужно инициализировать его занового.
		:type cache: bool
		:return: Манифест расширения.
		:rtype: ExtensionManifest
		"""

		if not parser: parser = self.__Parser
		if not extension: extension = self.__Extension
		parser = self.__CheckParser(parser)
		if cache and self.__ExtensionManifest and extension == self.__SystemObjects.extension_name: return self.__ExtensionManifest
		self.__ExtensionManifest = ExtensionManifest(self.__SystemObjects, parser, extension)

		return self.__ExtensionManifest

	def get_extension_settings(self, parser: str | None = None, extension: str | None = None, cache: bool = False) -> dict | None:
		"""
		Возвращает словарь настроек расширения.

		:param parser: Имя парсера. По умолчанию будет использовано последнее заданное.
		:type parser: str | None
		:param extension: Имя расширения. По умолчанию будет использовано последнее заданное.
		:type extension: str | None
		:param cache: Указывает, следует ли использовать кэш или прочитать данные заново.
		:type cache: bool
		:return: Словарь настроек или `None` в случае отсутствия файла.
		:rtype: dict | None
		"""

		if not parser: parser = self.__Parser
		if not extension: extension = self.__Extension
		parser = self.__CheckParser(parser)

		if cache and self.__ExtensionSettings and parser == self.__SystemObjects.parser_name and extension == self.__SystemObjects.extension_name: return self.__ExtensionSettings

		if not self.__ExtensionSettings:
			try: self.__ExtensionSettings = ReadJSON(f"Configs/{parser}/extensions/{extension}.json")
			except FileNotFoundError: pass

			if not self.__ExtensionSettings:

				try: 
					self.__ExtensionSettings = ReadJSON(f"Parsers/{parser}/extensions/{extension}/settings.json")
					self.__SystemObjects.logger.warning("Using extension settings from repository.", stdout = True)

				except FileNotFoundError: pass

		return self.__ExtensionSettings