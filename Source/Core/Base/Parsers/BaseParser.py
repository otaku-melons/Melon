from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseBranch, BaseTitle
from Source.Core.Base.Parsers.Components.ImagesDownloader import ImagesDownloader

from dublib.WebRequestor import WebConfig, WebLibs, WebRequestor
from dublib.Engine.Bus import ExecutionStatus
	
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.Components import ParserManifest, ParserSettings
	from Source.Core.Base.Formats.Components import WordsDictionary
	from Source.Core.SystemObjects import SystemObjects

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

	def _InitializeRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов."""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.set_retries_count(self._Settings.common.retries)
		Config.generate_user_agent()
		Config.add_header("Referer", f"https://{self._Manifest.site}/")
		Config.enable_proxy_protocol_switching(True)
		WebRequestorObject = WebRequestor(Config)
		WebRequestorObject.add_proxies(self._Settings.proxies)
		
		return WebRequestorObject

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", title: BaseTitle | None = None):
		"""
		Базовый парсер.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param title: Данные тайтла.
		:type title: BaseTitle | None
		"""

		self._SystemObjects = system_objects
		self._Title = title

		self._Temper = self._SystemObjects.temper
		self._Portals = self._SystemObjects.logger.portals
		self._Settings = self._SystemObjects.manager.current_parser_settings
		self._Manifest = self._SystemObjects.manager.current_parser_manifest

		self._Requestor = self._InitializeRequestor()
		self._ImagesDownloader = ImagesDownloader(self._SystemObjects, self._Requestor)

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

	def get_slug(self, data: str) -> ExecutionStatus:
		"""
		Получает алиас тайтла из переданной строки. Может использоваться для обработки тайтлов по ссылкам.

		:param data: Строка, из которой требуется получить алиас.
		:type data: str
		:return: Контейнер ответа. Значение должно содержать строку-алиас или `None`, если получить алиас не удалось.
		В данные статуса также помещается логический ключ _implemented_, говорящий об определении метода в парсере. Отсутствие ключа интерпретируется как наличие имплементации.
		:rtype: ExecutionStatus
		"""

		Status = ExecutionStatus()
		Status["implemented"] = False
		Status.value = data

		return Status

	def image(self, url: str) -> ExecutionStatus:
		"""
		Скачивает изображение по ссылке и сохраняет во временный каталог парсера.

		:param url: Ссылка на изображение.
		:type url: str
		:return: Статус выполнение, значение в котором должно содержать имя файла.
		:rtype: ExecutionStatus
		"""
		
		return self._ImagesDownloader.temp_image(url)

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