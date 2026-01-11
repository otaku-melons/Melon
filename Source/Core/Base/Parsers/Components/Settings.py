from Source.Core.SystemObjects.Logger import Logger
from Source.Core.Exceptions import BadSettings

from dublib.Methods.Filesystem import NormalizePath, ReadJSON
from dublib.WebRequestor import Proxy

from types import MappingProxyType
from os import PathLike
from typing import Any
import hashlib
import os
import re

#==========================================================================================#
# >>>>> СТАНДАРТНЫЕ НАСТРОЙКИ <<<<< #
#==========================================================================================#

Settings = MappingProxyType({
	"common": {
		"archives_directory": "",
		"images_directory": "",
		"titles_directory": "",
		"bad_image_stub": "",
		"pretty": False,
		"use_id_as_filename": False,
		"sizing_images": False,
		"retries": 1,
		"delay": 1
	},
	"filters": {
		"text_regexs": [],
		"text_strings": [],
		"image_md5": [],
		"image_min_height": None,
		"image_min_width": None,
		"image_max_height": None,
		"image_max_width": None
	},
	"proxies": [],
	"custom": {}
})

#==========================================================================================#
# >>>>> ДОПОЛНИТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class TextFilters:
	"""Фильтры текста."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def regexs(self) -> list[str]:
		"""Список регулярных выражений фильтрации."""

		return self.__Regexs
	
	@property
	def strings(self) -> list[str]:
		"""Список удаляемых строк."""

		return self.__Strings

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, data: dict):
		"""
		Фильтры текста.

		:param data: Словарь фильтров текста.
		:type data: dict
		"""

		self.__Regexs = list()
		self.__Strings = list()

		if "text_regexs" in data.keys() and type(data["text_regexs"]) == list: self.__Regexs = data["text_regexs"]
		if "text_strings" in data.keys() and type(data["text_strings"]) == list: self.__Strings = data["text_strings"]

	def clear(self, text: str) -> str:
		"""
		Очищает текст согласно фильтрам.

		:param text: Обрабатываемый текст.
		:type text: str
		:return: Обработанный текст.
		:rtype: str
		"""

		for Regex in self.__Regexs: text = re.sub(Regex, "", text)
		for String in self.__Strings: text = text.replace(String, "")

		return text

class ImageFilters:
	"""Фильтры изображений."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def md5(self) -> list[str]:
		"""Список MD5-хэшей нежелательных изображений."""

		return self.__Data["image_md5"]

	@property
	def min_height(self) -> int | None:
		"""Минимальная высота изображения."""

		return self.__Data["image_min_height"]
	
	@property
	def min_width(self) -> int | None:
		"""Минимальная ширина изображения."""

		return self.__Data["image_min_width"]
	
	@property
	def max_height(self) -> int | None:
		"""Максимальная высота изображения."""

		return self.__Data["image_max_height"]
	
	@property
	def max_width(self) -> int | None:
		"""Максимальная ширина изображения."""

		return self.__Data["image_max_width"]
	
	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, data: dict):
		"""
		Фильтры изображений.

		:param data: Словарь фильтров изображений.
		:type data: dict
		"""

		self.__Data = data

		if "image_md5" not in self.__Data.keys() or type(self.__Data["image_md5"]) != list: self.__Data["image_md5"] = list()
		Keys = ["image_min_height", "image_min_width", "image_max_height", "image_max_width"]

		for Key in Keys:
			if Key not in self.__Data.keys() or type(self.__Data[Key]) != int: self.__Data[Key] = None

	def check_hash(self, path: PathLike) -> bool:
		"""
		Проверяет, соответствует ли изображение указанным в чёрном списке MD5 хешам.

		:param path: Путь к изображению.
		:type path: str
		:return: Возвращает `True`, если хеш изображения найден в чёрном списке.
		:rtype: bool
		"""

		Hash = None
		
		with open(path, "rb") as FileReader: 
			BinaryContent = FileReader.read()
			Hash = hashlib.md5(BinaryContent).hexdigest()

		return Hash in self.md5

	def check_sizes(self, width: int, height: int) -> bool:
		"""
		Проверяет, выходит ли размер изображения за пределы разрешённых значений.

		:param width: Ширина изображения.
		:type width: int
		:param height: Высота изображения.
		:type height: int
		:return: Возвращает `True` при превышении одного из размеров.
		:rtype: bool
		"""

		IsFiltered = False

		if self.min_width and width < self.min_width: IsFiltered = True
		if self.min_height and height < self.min_height: IsFiltered = True
		if self.max_width and height > self.max_width: IsFiltered = True
		if self.max_height and height > self.max_height: IsFiltered = True

		return IsFiltered

#==========================================================================================#
# >>>>> КАТЕГОРИИ НАСТРОЕК <<<<< #
#==========================================================================================#

class Common:
	"""Базовые настройки."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def archives_directory(self) -> str:
		"""Директория читаемого контента."""

		return self.__Settings["archives_directory"]
	
	@property
	def bad_image_stub(self) -> str | None:
		"""Путь к заглушке плохого изображения."""

		return self.__Settings["bad_image_stub"]
	
	@property
	def images_directory(self) -> str:
		"""Директория изображений."""

		return self.__Settings["images_directory"]
	
	@property
	def titles_directory(self) -> str:
		"""Директория описательных файлов."""

		return self.__Settings["titles_directory"]
	
	@property
	def use_id_as_filename(self) -> bool:
		"""Указывает, нужно ли использовать ID в качестве имени описательного файла."""

		return self.__Settings["use_id_as_filename"]
	
	@property
	def sizing_images(self) -> bool:
		"""Указывает, нужно ли пытаться определить размер изображений."""

		return self.__Settings["sizing_images"]
	
	@property
	def pretty(self) -> bool:
		"""Состояние: включено ли улучшение качества контента."""

		return self.__Settings["pretty"]
	
	@property
	def retries(self) -> int:
		"""Количество повторов запроса при неудачном выполнении."""

		return self.__Settings["retries"]
	
	@property
	def delay(self) -> float:
		"""Интервал ожидания между последовательными запросами."""

		return self.__Settings["delay"]

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __PutDefaultDirectories(self, parser_name: str):
		"""
		Подстанавливает стандартные директории на пустые места.
		:param parser_name: Название парсера.
		:type parser_name: str
		:raises FileNotFoundError: Выбрасывается при указании несуществующей директории.
		"""

		Directories = ["archives", "images", "titles"]

		for Directory in Directories:
			Key = f"{Directory}_directory"

			if not self.__Settings[Key]:
				self.__Settings[Key] = f"Output/{parser_name}/{Directory}"
				if not os.path.exists(self.__Settings[Key]): os.makedirs(self.__Settings[Key])

			else:
				self.__Settings[Key] = NormalizePath(self.__Settings[Key])
				if not os.path.exists(self.__Settings[Key]): raise FileNotFoundError(self.__Settings[Key])

	def __init__(self, parser_name: str, settings: dict, logger: Logger):
		"""
		Базовые настройки.

		:param parser_name: Имя парсера.
		:type parser_name: str
		:param settings: Словарь настроек.
		:type settings: dict
		:param logger: Оператор логгирования.
		:type logger: Logger
		:raises BadSettings: Выбрасывается при обнаружении несоответствия формата файла насроек.
		"""

		self.__Settings = {
			"archives_directory": "",
			"images_directory": "",
			"titles_directory": "",
			"bad_image_stub": None,
			"pretty": False,
			"use_id_as_filename": False,
			"sizing_images": False,
			"retries": 0,
			"delay": 1.0
		}

		if "common" in settings.keys():
			if "delay" in settings["common"].keys(): settings["common"]["delay"] = float(settings["common"]["delay"])
			
			for Key in self.__Settings.keys():
				if Key in settings["common"].keys(): self.__Settings[Key] = settings["common"][Key]
				else: logger.warning(f"Setting \"{Key}\" has been reset to default.")

			if self.__Settings["bad_image_stub"]:
				BadImageStub = NormalizePath(self.__Settings["bad_image_stub"])
				if not os.path.exists(BadImageStub): self.__Settings["bad_image_stub"] = None
				else: self.__Settings["bad_image_stub"] = BadImageStub

			elif not self.__Settings["bad_image_stub"]: self.__Settings["bad_image_stub"] = None

			self.__PutDefaultDirectories(parser_name)

		else: raise BadSettings(parser_name)

class Directories:
	"""Директории."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def archives(self) -> str:
		"""Директория читаемого контента."""

		return self.__Common.archives_directory
	
	@property
	def images(self) -> str | None:
		"""Директория изображений."""

		return self.__Common.images_directory
	
	@property
	def titles(self) -> str:
		"""Директория описательных файлов."""

		return self.__Common.titles_directory

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __GenerateDirectoryPath(self, used_name: str, subdir: str) -> PathLike:
		"""
		Возвращает путь к подкаталогу изображений. Если такового нет, то создаёт его.

		:param used_name: Используемое имя тайтла.
		:type used_name: str
		:param subdir: Название подкаталога внутри директории изображений.
		:type subdir: str
		:return: Путь к подкаталогу изображений.
		:rtype: PathLike
		"""

		Directory = self.__Common.images_directory + f"/{used_name}/{subdir}"
		if not os.path.exists(Directory): os.makedirs(Directory)

		return Directory

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, common_settings: Common):
		"""
		Директории.

		:param common_settings: Базовые настройки.
		:type common_settings: Common
		"""

		self.__Common = common_settings

	def get_covers(self, used_name: str) -> PathLike:
		"""
		Возвращает путь к директории обложек. Если таковой нет, то создаёт её.

		:param used_name: Используемое имя тайтла.
		:type used_name: str
		:return: Путь к директории обложек.
		:rtype: PathLike
		"""

		return self.__GenerateDirectoryPath(used_name, "covers")
	
	def get_persons(self, used_name: str) -> PathLike:
		"""
		Возвращает путь к директории портретов персонажей. Если таковой нет, то создаёт её.

		:param used_name: Используемое имя тайтла.
		:type used_name: str
		:return: Путь к директории обложек.
		:rtype: PathLike
		"""

		return self.__GenerateDirectoryPath(used_name, "persons")

class Filters:
	"""Фильтры контента."""

	@property
	def text(self) -> TextFilters:
		"""Фильтры текста."""

		return self.__TextFilters
	
	@property
	def image(self) -> ImageFilters:
		"""Фильтры изображений."""

		return self.__ImageFilters

	def __init__(self, settings: dict):
		"""
		Фильтры контента.

		:param settings: Словарь настроек.
		:type settings: dict
		"""

		if "filters" not in settings.keys() or type(settings["filters"]) != dict: settings["filters"] = dict()
		self.__TextFilters = TextFilters(settings["filters"])
		self.__ImageFilters = ImageFilters(settings["filters"])

class Custom:
	"""Собственные настройки парсера."""

	def __init__(self, settings: dict, logger: Logger):
		"""
		Собственные настройки парсера.

		:param settings: Словарь настроек парсера.
		:type settings: dict
		:param logger: Оператор логгирования.
		:type logger: Logger
		"""

		self.__Settings = settings["custom"] if "custom" in settings.keys() else dict()
		self.__Logger = logger

	def __getitem__(self, key: str) -> Any:
		"""
		Возвращает значение настройки.

		:param key: Ключ настройки.
		:type key: str
		:return: Значение настройки.
		:rtype: Any
		"""

		if key not in self.__Settings.keys(): self.__Logger.warning(f"No custom setting: \"{key}\".")
		
		return self.__Settings[key]

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class ParserSettings:
	"""Настройки парсера."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def common(self) -> Common:
		"""Базовые настройки."""

		return self.__Common
	
	@property
	def directories(self) -> Directories:
		"""Директории."""

		return self.__Directories
	
	@property
	def filters(self) -> Filters:
		"""Фильтры контента."""

		return self.__Filters

	@property
	def custom(self) -> Custom:
		"""Собственные настройки парсера."""

		return self.__Custom
	
	@property
	def proxies(self) -> tuple[Proxy]:
		"""Набор прокси."""

		return self.__Proxies

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __ParseProxies(self, settings: dict) -> tuple[Proxy]:
		"""
		Парсит строковые представления прокси.

		:return: Набор объектов данных прокси.
		:rtype: tuple[Proxy]
		"""

		Proxies = list()

		if "proxies" in settings.keys():
			for String in settings["proxies"]: Proxies.append(Proxy().parse(String))
			
		return tuple(Proxies)

	def __ReadSettings(self) -> dict:
		"""
		Считывает настройки парсера из JSON в порядке приоритета: сначала из каталога конфигураций, затем из домашнего каталога парсера.

		:return: Словарь настроек парсера. При отстутствии таковых возвращает стандартный набор.
		:rtype: dict
		"""

		ParserSettingsDict = None
		Paths = [
			f"Configs/{self.__ParserName}/settings.json",
			f"Parsers/{self.__ParserName}/settings.json"
		]

		for Path in Paths:

			if os.path.exists(Path):
				ParserSettingsDict = ReadJSON(Path)
				if Path.startswith("Parsers"): self.__Logger.warning("Using parser settings from repository.", stdout = True)
				break

		if not ParserSettingsDict:
			self.__Logger.warning("Settings dropped to default values.")
			ParserSettingsDict = Settings.copy()

		return ParserSettingsDict

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, parser_name: str, logger: Logger):
		"""
		Настройки парсера.

		:param parser_name: Имя парсера.
		:type parser_name: str
		:param logger: Оператор логгирования.
		:type logger: Logger
		"""

		self.__ParserName = parser_name
		self.__Logger = logger

		self.__Settings = self.__ReadSettings()
		self.__Common = Common(parser_name, self.__Settings, logger)
		self.__Filters = Filters(self.__Settings)
		self.__Proxies = self.__ParseProxies(self.__Settings)
		self.__Custom = Custom(self.__Settings, logger)
		self.__Directories = Directories(self.__Common)