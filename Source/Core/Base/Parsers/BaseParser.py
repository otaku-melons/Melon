from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseBranch, BaseTitle
from Source.Core.Base.Parsers.Components.ImagesDownloader import ImagesDownloader
from Source.Core.Base.EntryPoint import BaseEntryPoint

from dublib.WebRequestor import WebRequestor
	
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.Components import ParserManifest, ParserSettings
	from Source.Core.Base.Formats.Components import WordsDictionary

class BaseParser:
	"""Базовый парсер."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def images_downloader(self) -> ImagesDownloader:
		"""Оператор скачивания изображений."""

		return self._ImagesDownloader

	@property
	def manifest(self) -> "ParserManifest":
		"""Манифест парсера."""

		return self._Manifest

	@property
	def requestor(self) -> WebRequestor:
		"""Менеджер запросов."""

		return self._Requestor

	@property
	def settings(self) -> "ParserSettings":
		"""Настройки парсера."""

		return self._Settings

	@property
	def title(self) -> BaseTitle:
		"""Данные тайтла."""

		return self._Title
	
	@property
	def words_dictionary(self) -> "WordsDictionary | None":
		"""Словарь ключевых слов."""

		return self._Title.words_dictionary

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, entry_point: "BaseEntryPoint", title: BaseTitle | None = None):
		"""
		Базовый парсер.

		:param entry_point: Точка входа в парсер.
		:type entry_point: BaseEntryPoint
		:param title: Данные тайтла.
		:type title: BaseTitle | None
		"""

		self._SystemObjects = entry_point.system_objects
		self._Title = title

		self._Temper = self._SystemObjects.temper
		self._Portals = self._SystemObjects.logger.portals
		self._SourceOperator = entry_point.source_operator
		self._Settings = entry_point.settings
		self._Manifest = entry_point.manifest

		self._Requestor = entry_point.source_operator.requestor
		self._ImagesDownloader = entry_point.source_operator.images_downloader

		self._PostInitMethod()

	def amend(self, branch: BaseBranch, chapter: BaseChapter):
		"""
		Дополняет главу дайными о слайдах.

		:param branch: Данные ветви.
		:type branch: BaseBranch
		:param chapter: Данные главы.
		:type chapter: BaseChapter
		"""

		pass

	def parse(self):
		"""Получает основные данные тайтла."""

		pass

	def postprocessor(self):
		"""Вносит изменения в тайтл непосредственно перед сохранением."""

		pass

	def set_title(self, title: BaseTitle):
		"""
		Задаёт данные тайтла.

		:param title: Данные тайтла.
		:type title: BaseTitle
		"""

		self._Title = title