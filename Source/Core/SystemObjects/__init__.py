from Source.Core.SystemObjects.Manager import Manager
from Source.Core.SystemObjects.Logger import Logger
from Source.Core.SystemObjects.Temper import Temper

from packaging.version import Version

from dulwich.contrib.release_robot import get_current_version

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class GlobalFlag:
	"""Глоабльный флаг."""

	@property
	def status(self) -> bool:
		"""Статус активации флага."""

		return self.__Value

	def __init__(self, status: bool):
		"""Глоабльный флаг."""

		self.__Value = status

	def __bool__(self) -> bool:
		"""Интерпретирует объект в логическое значение."""

		return self.__Value

	def disable(self):
		"""Отключает флаг."""

		self.__Value = False

	def enable(self):
		"""Включает флаг."""

		self.__Value = True

	def set_status(self, status: bool):
		"""
		Задаёт статус активации флага.

		:param status: Статус активации.
		:type status: bool
		"""

		self.__Value = status

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class SystemObjects:
	"""Коллекция системных объектов."""

	#==========================================================================================#
	# >>>>> ГЛОБАЛЬНЫЕ ФЛАГИ <<<<< #
	#==========================================================================================#

	@property
	def CACHING(self) -> GlobalFlag:
		"""Глоабльный флаг: включено ли кэширование объектов."""

		return self.__CachingEnabled

	@property
	def FORCE_MODE(self) -> GlobalFlag:
		"""Глоабльный флаг: включен ли режим перезаписи."""

		return self.__ForceMode
	
	@property
	def LIVE_MODE(self) -> GlobalFlag:
		"""Глоабльный флаг: активирован ли Live-режим."""

		return self.__LiveMode

	#==========================================================================================#
	# >>>>> ГЛОБАЛЬНЫЕ ДАННЫЕ <<<<< #
	#==========================================================================================#

	@property
	def MELON_VERSION(self) -> Version | None:
		"""Используемая версия Melon."""

		return Version("1.0.0")

		try: return Version(get_current_version())
		except TypeError: pass

	EXIT_CODE = 0

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def extension_name(self) -> str | None:
		"""Название используемого расширения."""

		return self.__ExtensionName

	@property
	def logger(self) -> Logger:
		"""Менеджер портов CLI и логов."""

		return self.__Logger

	@property
	def manager(self) -> Manager:
		"""Менеджер парсеров"""

		return self.__Manager
	
	@property
	def parser_name(self) -> str | None:
		"""Название используемого парсера."""

		return self.__ParserName

	@property
	def temper(self) -> Temper:
		"""Дескриптор каталога временных файлов."""

		return self.__Temper

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self):
		"""Коллекция системных объектов."""

		self.__Manager = Manager(self)
		self.__Logger = Logger(self)
		self.__Temper = Temper()

		self.__ExtensionName = None
		self.__ParserName = None

		self.__ForceMode = GlobalFlag(False)
		self.__LiveMode = GlobalFlag(False)
		self.__CachingEnabled = GlobalFlag(True)

	def select_extension(self, extension_name: str):
		"""
		Задаёт используемое расширение и настраивает согласно ему системные объекты.
			extension_name – имя расширения.
		"""

		self.__ExtensionName = extension_name
		self.__Manager.select_extension(extension_name)
		self.__Temper.select_extension(extension_name)

	def select_parser(self, parser_name: str):
		"""
		Задаёт используемое расширение и настраивает согласно ему системные объекты.
			parser_name – имя парсера.
		"""

		self.__ParserName = parser_name

		self.__Manager.select_parser(parser_name)
		self.__Logger.select_parser(parser_name)
		self.__Temper.select_parser(parser_name)