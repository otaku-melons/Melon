from .Formats.Components.Enums import ContentTypes
from .SourceOperator import BaseSourceOperator

from Source.Core.Base.Formats.Ranobe import Ranobe
from Source.Core.Base.Formats.Manga import Manga
from Source.Core import Exceptions

from dublib.Methods.Filesystem import ReadJSON

from types import MappingProxyType
from typing import TYPE_CHECKING
import importlib

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.Components import ParserManifest, ParserSettings
	from Source.Core.Base.Parsers.RanobeParser import RanobeParser
	from Source.Core.Base.Parsers.MangaParser import MangaParser
	from Source.Core.SystemObjects import SystemObjects

class BaseEntryPoint:
	"""Базовая точка входа в модуль парсера."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def is_supported_collect(self) -> bool:
		"""Состояние: поддерживается ли метод **collect**."""

		Module = importlib.import_module(f"Parsers.{self._Manifest.name}.main")

		try: Module.SourceOperator.collect
		except AttributeError: return False

		return True

	@property
	def manifest(self) -> "ParserManifest":
		"""Манифест парсера."""

		return self._Manifest

	@property
	def settings(self) -> "ParserSettings":
		"""Настройки парсера."""

		return self._SystemObjects.controller.get_parser_settings(self._Manifest.name)

	@property
	def source_operator(self) -> BaseSourceOperator:
		"""Базовый оператор источника."""

		if not self._SourceOperator:
			Module = importlib.import_module(f"Parsers.{self._Manifest.name}.main")
			self._SourceOperator = Module.SourceOperator(self)

		return self._SourceOperator

	@property
	def system_objects(self) -> "SystemObjects":
		"""Коллекция системных объектов."""

		return self._SystemObjects

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass
	
	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", manifest: "ParserManifest"):
		"""
		Базовая точка входа в модуль парсера.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param manifest: Манифест парсера.
		:type manifest: ParserManifest
		:param settings: Настройки парсера.
		:type settings: ParserSettings
		"""

		self._SystemObjects = system_objects
		self._Manifest = manifest

		self._SourceOperator: BaseSourceOperator | None = None
		self._ContentStructs = MappingProxyType({
			ContentTypes.Manga: Manga,
			ContentTypes.Ranobe: Ranobe
		})

		self._PostInitMethod()

	def create_title(self, content_type: ContentTypes, slug: str | None = None) -> "Manga | Ranobe":
		"""
		Создаёт тайтл определённого типа.

		:param content_type: Тип контента.
		:type content_type: ContentTypes
		:param slug: Алиас тайтла.
		:type slug: str | None
		:return: Данные тайтла.
		:rtype: Manga | Ranobe
		"""

		Title = self._ContentStructs[content_type](self._SystemObjects)
		if slug: Title.set_slug(slug)

		return Title

	def get_content_type_by_file(self, filename: str) -> ContentTypes:
		"""
		Определяет тип контента по JSON файлу.

		:param filename: Имя файла в выходном каталоге парсера.
		:type filename: str
		:return: Тип контента.
		:rtype: ContentTypes
		"""

		Path = f"{self.settings.directories.titles}/{filename}.json"
		Data = ReadJSON(Path)
		ContentType = Data.get("format").split("-")[-1]

		return ContentTypes(ContentType)

	def get_content_type_by_slug(self, slug: str) -> ContentTypes:
		"""
		Определяет тип контента по алиасу тайтла.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Тип контента.
		:rtype: ContentTypes
		"""

		SupportedTypes = self._Manifest.content_types

		if len(SupportedTypes) == 1: return SupportedTypes[0]
		else: raise Exceptions.BadEntryPoint("No content types specificator.")

	def launch_parser(self, content_type: ContentTypes) -> "MangaParser | RanobeParser":
		"""
		Запускает парсер определённого типа контента.

		:param content_type: Тип контента.
		:type content_type: ContentTypes
		:return: Объект парсера.
		:rtype: MangaParser | RanobeParser
		"""

		Module = importlib.import_module(f"Parsers.{self._Manifest.name}.{content_type.value}")
		Parser: "MangaParser | RanobeParser" = Module.Parser(self)

		return Parser