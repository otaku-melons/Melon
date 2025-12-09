from Source.Core.Base.Formats.Ranobe import Branch, Chapter, ChaptersTypes, Ranobe
from Source.Core.Base.Parsers.RanobeParser import RanobeParser
from Source.Core.Base.Formats.BaseFormat import Statuses

from dublib.Engine.Bus import ExecutionStatus
from dublib.WebRequestor import WebRequestor

class Parser(RanobeParser):
	"""Парсер."""
	
	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		# Оператор скачивания изображений.
		self._ImagesDownloader
		# Манифест парсера.
		self._Manifest
		# Коллекция унифицированных порталов вывода.
		self._Portals
		# Гибкий менеджер запросов.
		self._Requestor
		# Настройки парсера.
		self._Settings
		# Менеджер временного каталога парсера.
		self._Temper
		
		# Данные тайтла.
		self._Title

	def _InitializeRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов."""

		return super()._InitializeRequestor()

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def amend(self, branch: Branch, chapter: Chapter):
		"""
		Дополняет главу дайными о слайдах.

		:param branch: Данные ветви.
		:type branch: Branch
		:param chapter: Данные главы.
		:type chapter: Chapter
		"""

		pass

	def amend_postprocessor(self, chapter: Chapter):
		"""
		Вносит изменения в главу после дополнения её контентом. Запускается независимо от процесса дополнения.
		
		Переопределите данный метод для обработки.

		:param chapter: Данные главы.
		:type chapter: Chapter
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

		return super().get_slug(data)

	def image(self, url: str) -> ExecutionStatus:
		"""
		Скачивает изображение по ссылке и сохраняет во временный каталог парсера.

		:param url: Ссылка на изображение.
		:type url: str
		:return: Контейнер ответа. Значение должно содержать имя файла.
		:rtype: ExecutionStatus
		"""
		
		return super().image(url)

	def parse(self):
		"""Получает основные данные тайтла."""

		self._Title

		pass