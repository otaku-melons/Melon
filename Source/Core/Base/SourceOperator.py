from Source.Core.Base.Parsers.Components.ImagesDownloader import ImageDownloadingStatus, ImagesDownloader

from dublib.WebRequestor import WebConfig, WebLibs, WebRequestor
from dublib.Engine.Bus import ExecutionStatus
	
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .EntryPoint import BaseEntryPoint
	
	from Source.Core.Base.Parsers.Components import ParserManifest, ParserSettings

class BaseSourceOperator:
	"""Базовый оператор источника."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def images_downloader(self) -> ImagesDownloader:
		"""Оператор скачивания изображений."""

		return self._ImagesDownloader

	@property
	def parser_manifest(self) -> "ParserManifest":
		"""Манифест парсера."""

		return self._Manifest

	@property
	def parser_settings(self) -> "ParserSettings":
		"""Настройки парсера."""

		return self._Settings

	@property
	def requestor(self) -> WebRequestor:
		"""Менеджер запросов."""

		return self._Requestor

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

	def __init__(self, entry_point: "BaseEntryPoint"):
		"""
		Базовый оператор источника.

		:param entry_point: Точка входа в парсер.
		:type entry_point: BaseEntryPoint
		"""

		self._SystemObjects = entry_point.system_objects

		self._Temper = self._SystemObjects.temper
		self._Portals = self._SystemObjects.logger.portals
		self._Settings = entry_point.settings
		self._Manifest = entry_point.manifest

		self._Requestor = self._InitializeRequestor()
		self._ImagesDownloader = ImagesDownloader(self._SystemObjects, self._Requestor)

		self._PostInitMethod()

	def collect(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> tuple[str]:
		"""
		Собирает список алиасов тайтлов по заданным параметрам.

		:param period: Количество часов до текущего момента, составляющее период получения данных.
		:type period: int | None
		:param filters: Строка, описывающая фильтрацию (подробнее в README.md парсера).
		:type filters: str | None
		:param pages: Количество запрашиваемых страниц каталога.
		:type pages: int | None
		:return: Набор собранных алиасов.
		:rtype: tuple[str]
		"""

		return tuple()

	def get_slug_from_string(self, data: str) -> ExecutionStatus:
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

	def image(self, url: str) -> ImageDownloadingStatus:
		"""
		Скачивает изображение по ссылке и сохраняет во временный каталог парсера.

		:param url: Ссылка на изображение.
		:type url: str
		:return: Статус скачивания изображения. В случае успеха значение должно содержать имя файла во временном каталоге парсера.
		:rtype: ImageDownloadingStatus
		"""
		
		return self._ImagesDownloader.temp_image(url)