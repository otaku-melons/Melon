from Source.Core.Exceptions import TempOwnerNotSpecified

from dublib.Methods.Filesystem import ReadJSON, RemoveDirectoryContent, WriteJSON

from typing import Iterable
from os import PathLike
import shutil
import os

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class Journal:
	"""Журнал хранения пар ID-алиас тайтлов."""

	def __init__(self, shared_data: "SharedData"):
		"""
		Журнал хранения пар ID-алиас тайтлов.

		:param shared_data: Разделяемые в контексте одного парсера данные.
		:type shared_data: SharedData
		"""

		self.__SharedData = shared_data

		self.__Data = dict()

	def get_id_by_slug(self, slug: str) -> int | None:
		"""
		Ищет ID тайтла по его алиасу.

		:param slug: Алиас тайтла.
		:type slug: str
		"""

		for ID, Slug in self.__Data.items():
			if slug == Slug: return int(ID)

	def get_slug_by_id(self, title_id: int) -> str | None:
		"""
		Ищет алиас тайтла по его ID.

		:param slug: Алиас тайтла.
		:type slug: str
		"""

		try: return self.__Data[str(title_id)]
		except KeyError: pass

	def drop(self):
		"""Сбрасывает журнал."""

		self.__Data = dict()
		self.save()

	def load(self):
		"""Загружает журнал."""

		Path = f"{self.__SharedData.path}/journal.json"
		if os.path.exists(Path): self.__Data = ReadJSON(Path)

	def save(self):
		"""Сохраняет журнал."""

		self.__Data = {Key: self.__Data[Key] for Key in sorted(self.__Data.keys(), key = int)}
		WriteJSON(f"{self.__SharedData.path}/journal.json", self.__Data)

	def update(self, title_id: int, slug: str):
		"""
		Обновляет запись об алиасе тайтла.

		:param title_id: ID тайтла.
		:type title_id: int
		:param slug: Алиас тайтла.
		:type slug: str
		:raise TypeError: Выбрасывается при неверном типе переданных данных.
		"""

		if type(title_id) != int: raise TypeError("Title ID must be integer.")
		if type(slug) != str: raise TypeError("Title slug must be string.")
		self.__Data[str(title_id)] = slug
		self.save()

class SharedData:
	"""Разделяемые в контексте одного парсера данные."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def journal(self) -> Journal:
		"""Журнал определений тайтлов."""

		return self.__Journal

	@property
	def last_parsed_slug(self) -> str | None:
		"""Алиас последнего тайтла, обработанного парсером."""

		return self.__Data["last_parsed_slug"]

	@property
	def path(self) -> PathLike:
		"""Путь к каталогу разделяемых данных."""

		Path = f"{self.__Temper.parser_temp}/shared"
		if not os.path.exists(Path): os.makedirs(Path)

		return Path

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	def __init__(self, temper: "Temper"):
		"""
		Разделяемые в контексте одного парсера данные.

		:param temper: Дескриптор временных каталогов и объектов.
		:type temper: Temper
		"""

		self.__Temper = temper

		self.__Journal = Journal(self)
		self.__Data = {
			"last_parsed_slug": None
		}

	def load(self):
		"""Загружает разделяемые данные."""

		Path = f"{self.path}/shared.json"
		if os.path.exists(Path): self.__Data = ReadJSON(Path)
		self.__Journal.load()

	def set_last_parsed_slug(self, slug: str):
		"""
		Задаёт алиас последнего обработанного парсером тайтла.

		:param slug: Алиас.
		:type slug: str
		"""

		self.__Data["last_parsed_slug"] = slug
		self.save()
		
	def save(self):
		"""Сохраняет разделяемые данные."""

		WriteJSON(f"{self.path}/shared.json", self.__Data)

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Temper:
	"""Дескриптор временных каталогов и объектов."""

	#==========================================================================================#
	# >>>>> ПУТИ К КАТАЛОГАМ <<<<< #
	#==========================================================================================#

	@property
	def builder_temp(self) -> PathLike:
		"""Путь к выделенному для сборки контента каталогу временных файлов."""

		Path = f"{self.parser_temp}/build"
		if not os.path.exists(Path): os.makedirs(Path)

		return Path

	@property
	def extension_temp(self) -> PathLike:
		"""Путь к выделенному для конкретного расширения каталогу временных файлов."""

		if not self.__ParserName or not self.__ExtensionName: raise TempOwnerNotSpecified()
		Path = f"{self.__Temp}/{self.__ParserName}/extensions/{self.__ExtensionName}"
		if not os.path.exists(Path): os.makedirs(Path)

		return Path

	@property
	def parser_temp(self) -> PathLike:
		"""Путь к выделенному для конкретного парсера каталогу временных файлов."""

		if not self.__ParserName: raise TempOwnerNotSpecified()
		Path = f"{self.__Temp}/{self.__ParserName}"
		os.makedirs(Path, exist_ok = True)

		return Path

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def shared_data(self) -> SharedData:
		"""Разделяемые в контексте одного парсера данные."""

		return self.__SharedData

	@property
	def whitelist(self) -> tuple[str]:
		"""Список имён файлов и каталогов, по умолчанию не удаляемых при очистке."""

		return self.__StandartWhitelist + self.__CustomWhitelist

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, parser: str | None = None, extension: str | None = None):
		"""
		Дескриптор временных каталогов и объектов.

		:param parser: Имя парсера.
		:type parser: str | None
		:param extension: Имя расширения.
		:type extension: str | None
		"""

		self.__ParserName = parser
		self.__ExtensionName = extension

		self.__Temp = "Temp"
	
		self.__SharedData = SharedData(self)

		self.__StandartWhitelist = ("Collection.txt", "shared")
		self.__CustomWhitelist = tuple()

	def clear_parser_temp(self, full: bool = False):
		"""
		Очищает временный каталог парсера. По умолчанию не трогает файлы и каталоги из белого списка.

		:param full: Если указать `True`, будут удалены также файлы и каталоги и из белого списка.
		:type full: bool
		"""

		if full: 
			RemoveDirectoryContent(self.parser_temp)
			return

		for Descriptor in os.scandir(self.parser_temp):
			if Descriptor.name in self.whitelist: continue

			if Descriptor.is_file(): os.remove(Descriptor.path)
			elif Descriptor.is_dir(): shutil.rmtree(Descriptor.path)

	def select_extension(self, extension: str):
		"""
		Задаёт имя используемого расширения.

		:param extension: Имя расширения.
		:type extension: str
		"""

		self.__ExtensionName = extension

	def select_parser(self, parser_name: str):
		"""
		Задаёт имя используемого парсера.

		:param parser_name: Имя парсера.
		:type parser_name: str
		"""

		self.__ParserName = parser_name
		self.__SharedData.load()

	def set_whitelist(self, whitelist: Iterable[str]):
		"""
		Задаёт белый список имён файлов и каталогов, по умолчанию не удаляемых при очистке.

		:param whitelist: Последовательность имён файлов и каталогов.
		:type whitelist: Iterable[str]
		"""

		self.__CustomWhitelist = tuple(whitelist)