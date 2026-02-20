from .Components.WordsDictionary import CheckLanguageCode, GetDictionaryPreset, WordsDictionary
from .Components.Functions import SafelyReadTitleJSON
from .Components.Structs import *

from Source.Core import Exceptions

from dublib.Methods.Data import RemoveRecurringSubstrings, Zerotify
from dublib.Methods.Filesystem import WriteJSON

from typing import Any, Iterable, TYPE_CHECKING
from dataclasses import dataclass
from os import PathLike
from time import sleep
import os

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.RanobeParser import Chapter as RanobeChapter
	from Source.Core.Base.Parsers.MangaParser import Chapter as MangaChapter
	from Source.Core.Base.Parsers.BaseParser import BaseParser
	from Source.Core.SystemObjects import SystemObjects

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

@dataclass
class ChapterSearchResult:
	branch: "BaseBranch"
	chapter: "BaseChapter"

class Person:
	"""Данные персонажа."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def name(self) -> str:
		"""Имя."""

		return self.__Data["name"]

	@property
	def another_names(self) -> list[str]:
		"""Альтернативные имена."""

		return self.__Data["another_names"]

	@property
	def images(self) -> list[dict]:
		"""Список данных портретов."""

		return self.__Data["images"]

	@property
	def description(self) -> str | None:
		"""Описание."""

		return self.__Data["description"]
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, name: str):
		"""
		Данные персонажа.
			name – имя персонажа.
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__Data = {
			"name": name,
			"another_names": [],
			"images": [],
			"description": None
		}

	def add_another_name(self, another_name: str):
		"""
		Добавляет альтернативное имя.
			another_name – имя.
		"""
		
		another_name = another_name.strip()
		if another_name and another_name != self.name and another_name not in self.another_names: self.__Data["another_names"].append(another_name)

	def add_image(self, link: str, filename: str | None = None, width: int | None = None, height: int | None = None):
		"""
		Добавляет портрет.
			link – ссылка на изображение;\n
			filename – имя локального файла;\n
			width – ширина обложки;\n
			height – высота обложки.
		"""

		if not filename: filename = link.split("/")[-1]
		CoverInfo = {
			"link": link,
			"filename": filename,
			"width": width,
			"height": height
		}

		self.__Data["images"].append(CoverInfo)

	def set_description(self, description: str | None):
		"""
		Задаёт описание.
			description – описание.
		"""

		self.__Data["description"] = Zerotify(description)

	def to_dict(self, sizing_images: bool = True) -> dict:
		"""
		Возвращает словарное представление данных персонажа.

		:param sizing_images: Указывает, нужно ли указать размеры изображений персонажа.
		:type sizing_images: bool
		:return: Словарное представление данных персонажа.
		:rtype: dict
		"""

		Data = self.__Data.copy()

		if not sizing_images:

			for Index in range(len(Data["images"])):
				del Data["images"][Index]["width"]
				del Data["images"][Index]["height"]

		return Data

class BaseChapter:
	"""Базовая глава."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def id(self) -> int | None:
		"""Уникальный идентификатор главы."""

		return self._Chapter["id"]
	
	@property
	def slug(self) -> str | None:
		"""Алиас главы."""

		return self._Chapter["slug"]
	
	@property
	def is_empty(self) -> bool:
		"""Состояние: содержит ли глава контент."""

		IsEmpty = True
		if "slides" in self._Chapter.keys() and self._Chapter["slides"]: IsEmpty = False
		elif "paragraphs" in self._Chapter.keys() and self._Chapter["paragraphs"]: IsEmpty = False

		return IsEmpty

	@property
	def volume(self) -> str | None:
		"""Номер тома."""

		return self._Chapter["volume"]
	
	@property
	def number(self) -> str | None:
		"""Номер главы."""

		return self._Chapter["number"]
	
	@property
	def name(self) -> str | None:
		"""Название главы."""

		return self._Chapter["name"]

	@property
	def is_paid(self) -> bool | None:
		"""Состояние: платная ли глава."""

		return self._Chapter["is_paid"]
	
	@property
	def workers(self) -> tuple[str]:
		"""Набор идентификаторов лиц, адаптировавших контент."""

		return tuple(self._Chapter["workers"])
	
	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __PrettyNumber(self, number: str | None) -> str | None:
		"""Преобразует номер главы или тома в корректное значение."""

		if number == None: number = ""
		elif type(number) != str: number = str(number)
		if "-" in number: number = number.split("-")[0]
		number = number.strip("\t .\n")
		number = Zerotify(number)

		return number

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _Pass(self, value: Any):
		"""Заглушка Callable-объекта для неактивных методов установки контента."""

		pass

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", title: "BaseTitle | None" = None):
		"""
		Базовая глава.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param title: Данные тайтла.
		:type title: BaseTitle | None
		"""

		self._SystemObjects = system_objects
		self._Title = title

		self._Chapter = {
			"id": None,
			"slug": None,
			"volume": None,
			"number": None,
			"name": None,
			"is_paid": None,
			"workers": []
		}

		self._SetParagraphsMethod = self._Pass
		self._SetSlidesMethod = self._Pass

	def __getitem__(self, key: str) -> Any:
		"""
		Возвращает значение из внутреннего словаря.

		:param key: Ключ.
		:type key: str
		:raise KeyError: Выбрасывается при отсутствии ключа в данных главы.
		:return: Значение.
		:rtype: Any
		"""

		return self._Chapter[key]

	def __setitem__(self, key: str, value: Any):
		"""
		Устанавливает значение напрямую в структуру данных по ключу.

		:param key: Ключ.
		:type key: str
		:param value: Значение.
		:type value: Any
		"""

		self._Chapter[key] = value

	def add_extra_data(self, key: str, value: Any):
		"""
		Добавляет дополнительные данные о главе.
			key – ключ для доступа;\n
			value – значение.
		"""

		self._Chapter[key] = value

	def add_worker(self, worker: str):
		"""
		Добавляет идентификатор лица, адаптировавшего контент.

		:param worker: Идентификатор.
		:type worker: str
		"""

		if worker: self._Chapter["workers"].append(worker)

	def clear(self):
		"""Удаляет содержимое главы."""

		for ContentKey in ("slides", "paragraphs"):
			if self._Chapter.get(ContentKey):
				self._Chapter[ContentKey] = list()
				break

	def remove_extra_data(self, key: str):
		"""
		Удаляет дополнительные данные главы.

		:param key: Ключ, под которым хранятся дополнительные данные.
		:type key: str
		"""

		try: del self._Chapter[key]
		except KeyError: pass

	def set_dict(self, dictionary: dict, use_methods: bool = False):
		"""
		Напрямую задаёт словарь, используемый в качестве хранилища данных главы.

		:param dictionary: Данные главы. Будет создана копия.
		:type dictionary: dict
		:param use_methods: Если включить, вместо прямой перезаписи словаря все значения будут установлены через соответствующие методы с валидацией.
		:type use_methods: bool
		"""

		dictionary = dictionary.copy()

		if not use_methods:
			self._Chapter = dictionary
			return
		
		#---> Установка свойств через доступные методы.
		#==========================================================================================#
		KeyMethods = {
			"id": self.set_id,
			"volume": self.set_volume,
			"name": self.set_name,
			"is_paid": self.set_is_paid,
			"workers": self.set_workers,
		}

		for Key in KeyMethods.keys():
			
			if Key in dictionary:
				Value = dictionary[Key]
				KeyMethods[Key](Value)
				del dictionary[Key]

		#---> Слияние контетна.
		#==========================================================================================#
		for Key in ("slides", "paragraphs"):
			if Key in dictionary:
				self._Chapter[Key] = dictionary[Key]
				del dictionary[Key]
				break

		#---> Добавление дополнительных данных.
		#==========================================================================================#
		for Key in dictionary.keys(): self.add_extra_data(Key, dictionary[Key])

	def set_id(self, id: int | None):
		"""
		Задаёт уникальный идентификатор главы.
			ID – идентификатор.
		"""

		self._Chapter["id"] = id

	def set_is_paid(self, is_paid: bool | None):
		"""
		Указывает, является ли глава платной.
			is_paid – состояние: платная ли глава.
		"""

		self._Chapter["is_paid"] = is_paid

	def set_name(self, name: str | None):
		"""
		Задаёт название главы.

		:param name: Название главы.
		:type name: str | None
		"""

		name = Zerotify(name)
		if name: name = name.strip()
		
		if name and self._SystemObjects.manager.current_parser_settings.common.pretty:
			if name.endswith("..."): name = name.rstrip(".") + "…"
			else: name = name.rstrip(".–")
		
			name = name.replace("\u00A0", " ")
			name = RemoveRecurringSubstrings(name, " ")

			name = name.rstrip(":.")

		self._Chapter["name"] = name

	def set_number(self, number: float | int | str | None):
		"""
		Задаёт номер главы.
			number – номер главы.
		"""
		
		self._Chapter["number"] = self.__PrettyNumber(number)

	def set_workers(self, workers: Iterable[str]):
		"""
		Задаёт идентификаторы лиц, адаптировавших контент.

		:param workers: Набор идентификаторов.
		:type workers: Iterable[str]
		"""

		for Worker in workers: self.add_worker(Worker)

	def set_slug(self, slug: str | None):
		"""
		Задаёт алиас главы.
			slug – алиас.
		"""

		self._Chapter["slug"] = slug

	def set_volume(self, volume: float | int | str | None):
		"""
		Задаёт номер тома.
			volume – номер тома.
		"""

		self._Chapter["volume"] = self.__PrettyNumber(volume)

	def to_dict(self) -> dict:
		"""Возвращает словарь данных главы."""

		return self._Chapter
	
class BaseBranch:
	"""Базовая ветвь."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def chapters(self) -> list[BaseChapter]:
		"""Список глав."""

		return self._Chapters

	@property
	def chapters_count(self) -> int:
		"""Количество глав."""

		return len(self._Chapters)

	@property
	def empty_chapters_count(self) -> int:
		"""Количество глав без контента."""

		EmptyChaptersCount = 0

		for CurrentChapter in self._Chapters:

			try:
				if not CurrentChapter.slides: EmptyChaptersCount += 1

			except AttributeError:
				if not CurrentChapter.paragraphs: EmptyChaptersCount += 1

		return EmptyChaptersCount

	@property
	def id(self) -> int:
		"""Уникальный идентификатор ветви."""

		return self._ID
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, id: int):
		"""
		Базовая ветвь.

		:param id: Уникальный идентификатор ветви.
		:type id: int
		"""

		self._ID = id
		self._Chapters: list[BaseChapter] = list()

	def add_chapter(self, chapter: BaseChapter):
		"""
		Добавляет главу в ветвь. Если глава с таким ID уже существует, добавление не происходит.

		:param chapter: Данные главы.
		:type chapter: BaseChapter
		:raises ParsingError: Выбрасывается при отсутствии у добавляемой главы ID.
		"""

		if chapter.id == None: raise Exceptions.ParsingError("Chapter must have unique ID.")
		if chapter.id in tuple(Value.id for Value in self._Chapters): return
		self._Chapters.append(chapter)

	def get_chapter_by_id(self, id: int) -> BaseChapter:
		"""
		Возвращает главу по её уникальному идентификатору.
			id – идентификатор главы.
		"""

		Data = None

		for CurrentChapter in self._Chapters:
			if CurrentChapter.id == id: Data = CurrentChapter

		if not Data: raise KeyError(id)

		return CurrentChapter
	
	def replace_chapter_by_id(self, chapter: BaseChapter, id: int):
		"""
		Заменяет главу по её уникальному идентификатору.
			id – идентификатор главы.
		"""

		IsSuccess = False

		for Index in range(len(self._Chapters)):

			if self._Chapters[Index].id == id:
				self._Chapters[Index] = chapter
				IsSuccess = True

		if not IsSuccess: raise KeyError(id)
	
	def reverse(self):
		"""Инвертирует порядок глав в ветви."""

		self._Chapters = list(reversed(self._Chapters))

	def sort(self):
		"""
		По умолчанию помещает главы в порядке возрастания их нумерации.

		Переопределите данный метод для использования иных алгоритмов сортировки.
		"""

		self._Chapters = list(sorted(
			self._Chapters,
			key = lambda Value: (
				list(map(int, Value.volume.split(".") if Value.volume else "")),
				list(map(int, Value.number.split(".") if Value.number else ""))
			)
		))

	def to_list(self) -> list[dict]:
		"""Возвращает список словарей данных глав, принадлежащих текущей ветви."""

		BranchList = list()
		for CurrentChapter in self._Chapters: BranchList.append(CurrentChapter.to_dict())

		return BranchList
	
#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class BaseTitle:
	"""Базовый тайтл."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def parser(self) -> "BaseParser":
		"""Установленный парсер контента."""

		return self._Parser
	
	@property
	def path(self) -> PathLike | None:
		"""Путь к локальному файлу."""

		return self._TitlePath

	@property
	def used_filename(self) -> str | None:
		"""Используемое имя файла."""

		return self._UsedFilename

	@property
	def words_dictionary(self) -> WordsDictionary | None:
		"""Словарь ключевых слов."""

		return self._WordsDictionary

	#==========================================================================================#
	# >>>>> СВОЙСТВА ТАЙТЛА <<<<< #
	#==========================================================================================#

	@property
	def format(self) -> str | None:
		"""Формат структуры данных."""

		return self._Title["format"]

	@property
	def site(self) -> str | None:
		"""Домен целевого сайта."""

		return self._Title["site"]

	@property
	def id(self) -> int | None:
		"""Целочисленный уникальный идентификатор тайтла."""

		return self._Title["id"]

	@property
	def slug(self) -> str | None:
		"""Алиас."""

		return self._Title["slug"]
	
	@property
	def content_language(self) -> str | None:
		"""Код языка контента по стандарту ISO 639-3."""

		return self._Title["content_language"]

	@property
	def localized_name(self) -> str | None:
		"""Локализованное название."""

		return self._Title["localized_name"]

	@property
	def eng_name(self) -> str | None:
		"""Название на английском."""

		return self._Title["eng_name"]

	@property
	def another_names(self) -> list[str]:
		"""Список альтернативных названий."""

		return self._Title["another_names"]

	@property
	def content_language(self) -> str | None:
		"""Язык контента по стандарту ISO 639-3."""

		return self._Title["content_language"]
	
	@property
	def covers(self) -> list[dict]:
		"""Список описаний обложки."""

		return self._Title["covers"]

	@property
	def authors(self) -> list[str]:
		"""Список авторов."""

		return self._Title["authors"]

	@property
	def publication_year(self) -> int | None:
		"""Год публикации."""

		return self._Title["publication_year"]

	@property
	def description(self) -> str | None:
		"""Описание."""

		return self._Title["description"]

	@property
	def age_limit(self) -> int | None:
		"""Возрастное ограничение."""

		return self._Title["age_limit"]

	@property
	def genres(self) -> list[str]:
		"""Список жанров."""

		return self._Title["genres"]

	@property
	def tags(self) -> list[str]:
		"""Список тегов."""

		return self._Title["tags"]

	@property
	def franchises(self) -> list[str]:
		"""Список франшиз."""

		return self._Title["franchises"]
	
	@property
	def perons(self) -> list[Person]:
		"""Список персонажей."""

		return self._Persons
	
	@property
	def status(self) -> Statuses | None:
		"""Статус тайтла."""

		return self._Title["status"]

	@property
	def is_licensed(self) -> bool | None:
		"""Состояние: лицензирован ли тайтл на данном ресурсе."""

		return self._Title["is_licensed"]

	@property
	def branches(self) -> list[BaseBranch]:
		"""Список ветвей тайтла."""

		return self._Branches
	
	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _CalculateEmptyChapters(self) -> int:
		"""Подсчитывает количество глав без контента во всех ветвях."""

		EmptyChaptersCount = 0
		for Branch in self._Branches: EmptyChaptersCount += Branch.empty_chapters_count

		return EmptyChaptersCount

	def _CheckStringsList(self, data: list[str]) -> list:
		"""
		Проверяет, содержит ли список только валидные строки.
			data – список объектов.
		"""

		List = list()

		for Element in data:
			if type(Element) != str: raise TypeError(Element)
			elif Element: List.append(Element)

		return List

	def _DownloadCovers(self):
		"""Скачивает обложки."""

		CoversDirectory = self._ParserSettings.directories.get_covers(self._UsedFilename)
		DownloadedCoversCount = 0
		CoversCount = len(self._Title["covers"])

		for CoverIndex in range(CoversCount):
			Link = self._Title["covers"][CoverIndex]["link"]
			Filename = self._Title["covers"][CoverIndex]["filename"]
			IsExists = self._Parser.images_downloader.is_exists(Link, CoversDirectory, Filename)
			print(f"Downloading cover: \"{Filename}\"… ", end = "", flush = True)

			if IsExists and not self._SystemObjects.FORCE_MODE:
				print("Already exists.")
				continue

			Result = self._Parser.image(Link)
			
			if Result.code == 200:
				self._Parser.images_downloader.move_from_temp(CoversDirectory, Result.value, Filename)
				if IsExists: print("Overwritten.")
				else: print("Done.")

				if self._ParserSettings.common.sizing_images:
					self._Title["covers"][CoverIndex]["width"] = Result["resolution"].width
					self._Title["covers"][CoverIndex]["height"] = Result["resolution"].height

				DownloadedCoversCount += 1

			if CoverIndex < CoversCount - 1: sleep(self._ParserSettings.common.delay)

		self._SystemObjects.logger.info(f"Covers downloaded: {DownloadedCoversCount}.")

	def _DownloadPersonsImages(self):
		"""Скачивает портреты персонажей."""

		if self._Persons: PersonsDirectory = self._ParserSettings.directories.get_persons(self._UsedFilename)
		DownloadedImagesCount = 0
		PersonsCount = len(self._Persons)

		for PersonIndex in range(PersonsCount):

			for ImageData in self._Persons[PersonIndex].images:
				Link = ImageData["link"]
				Filename = ImageData["filename"]
				IsExists = self._Parser.images_downloader.is_exists(Link, PersonsDirectory, Filename)
				print(f"Downloading person image: \"{Filename}\"… ", end = "", flush = True)
				
				if IsExists and not self._SystemObjects.FORCE_MODE:
					print("Already exists.")
					continue

				Result = self._Parser.image(Link)
			
				if Result.code == 200:
					self._Parser.images_downloader.move_from_temp(PersonsDirectory, Result.value, Filename)
					if IsExists: print("Overwritten.")
					else: print("Done.")
					DownloadedImagesCount += 1

				if PersonIndex < PersonsCount - 1: sleep(self._ParserSettings.common.delay)

		self._SystemObjects.logger.info(f"Presons images downloaded: {DownloadedImagesCount}.")

	def _FindChapterByID(self, chapter_id: int) -> ChapterSearchResult | None:
		"""
		Возвращает данные ветви и главы для указанного ID.
			chapter_id – уникальный идентификатор главы.
		"""

		BranchResult = None
		ChapterResult = None

		for CurrentBranch in self._Branches:

			for CurrentChapter in CurrentBranch.chapters:

				if CurrentChapter.id == chapter_id:
					BranchResult = CurrentBranch
					ChapterResult = CurrentChapter
					break

		Result = ChapterSearchResult(BranchResult, ChapterResult) if ChapterResult else None

		return Result
	
	def _SearchFileInDirectory(self, directory: PathLike, identificator: str, type: By) -> dict | None:
		"""
		Находит файл JSON в директории по идентификатору определённого типа.

		:param directory: Путь к каталогу файлов.
		:type directory: PathLike
		:param identificator: Идентификатор: ID или алиас.
		:type identificator: str
		:param type: Тип идентификатора: `By.Slug` или `By.ID`.
		:type type: By
		:return: Содержимое файла или `None` при отсутствии оного или ошибке.
		:rtype: dict | None
		"""

		for Element in os.scandir(directory):
			if not Element.is_file() or not Element.name.endswith(".json"): continue

			try: 
				Data = SafelyReadTitleJSON(Element.path)
				if Data.get(type.value) == identificator: return Data

			except: pass

	def _SetUsedFilename(self, filename: str):
		"""
		Обновляет путь к локальному файлу JSON на основе используемого имени.

		:param filename: Используемое имя файла.
		:type filename: str
		"""

		self._UsedFilename = filename
		self._TitlePath = f"{self._ParserSettings.common.titles_directory}/{filename}.json"

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ ОБНОВЛЕНИЯ СЛОВАРНОЙ СТРУКТУРЫ <<<<< #
	#==========================================================================================#

	def _UpdateBranchesInfo(self):
		"""Обновляет информацию о ветвях."""

		Branches = list()
		for CurrentBranch in self._Branches: Branches.append({"id": CurrentBranch.id, "chapters_count": CurrentBranch.chapters_count})
		self._Title["branches"] = sorted(Branches, key = lambda Value: Value["chapters_count"], reverse = True)

	def _UpdateContent(self, brach_id: int | None = None, sorting: bool = True):
		"""
		Обновляет контент во внутреннем словарном хранилище данных тайтла.

		:param brach_id: Если указать ID ветви, будет обновлена только одна ветвь.
		:type brach_id: int | None
		:param sorting: Указывает, нужно ли провести сортировку глав на основе их нумерации.
		:type sorting: bool
		"""

		for CurrentBranch in self._Branches:
			if brach_id and brach_id == CurrentBranch.id or not brach_id:
				if sorting: CurrentBranch.sort()
				self._Title["content"][str(CurrentBranch.id)] = CurrentBranch.to_list()
				if brach_id: break

	def _UpdatePersons(self):
		"""Обновляет данные персонажей во внутреннем словарном хранилище данных тайтла."""

		self._Title["persons"] = list()

		for CurrentPerson in self._Persons:
			self._Title["persons"].append(CurrentPerson.to_dict(self._ParserSettings.common.sizing_images))

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _ParseBranchesToObjects(self):
		"""Преобразует данные ветвей в объекты."""

		pass

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def merge(self):
		"""Выполняет слияние содержимого описанных локально глав с текущей структурой."""

		raise Exceptions.MergingError("Called not implemented method.")

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Базовый тайтл.
			system_objects – коллекция системных объектов.
		"""

		self._SystemObjects = system_objects

		self._ParserSettings = self._SystemObjects.manager.current_parser_settings
		self._Branches: list[BaseBranch] = list()
		self._Persons: list[Person] = list()
		self._Parser: "BaseParser" = None
		self._WordsDictionary: WordsDictionary | None = None
		
		self._UsedFilename = None
		self._TitlePath = None
		self._Title = {
			"format": None,
			"site": None,
			"id": None,
			"slug": None,
			"content_language": None,

			"localized_name": None,
			"eng_name": None,
			"another_names": [],
			"covers": [],

			"authors": [],
			"publication_year": None,
			"description": None,
			"age_limit": None,

			"status": None,
			"is_licensed": None,
			
			"genres": [],
			"tags": [],
			"franchises": [],
			"persons": [],
			
			"branches": [],
			"content": {} 
		}

		self._PostInitMethod()

	def amend(self):
		"""Дополняет контент содержимым."""

		AmendedChaptersCount = 0
		ProgressIndex = 0

		if not self._Branches:
			self._SystemObjects.logger.info("No content for amending.")
			return

		for CurrentBranch in self._Branches:

			for CurrentChapter in CurrentBranch.chapters:
				CurrentChapter: "MangaChapter | RanobeChapter"
				ChapterContent = list()

				if self.format == "melon-manga": ChapterContent = CurrentChapter.slides
				elif self.format == "melon-ranobe": ChapterContent = CurrentChapter.paragraphs

				if not ChapterContent:
					ProgressIndex += 1
					
					try: self._Parser.amend(CurrentBranch, CurrentChapter)
					except Exceptions.ChapterNotFound: continue

					if self.format == "melon-manga": ChapterContent = CurrentChapter.slides
					elif self.format == "melon-ranobe": ChapterContent = CurrentChapter.paragraphs

					if ChapterContent:
						AmendedChaptersCount += 1
						self._SystemObjects.logger.chapter_amended(CurrentChapter)
						sleep(self._ParserSettings.common.delay)

					else:
						self._SystemObjects.logger.warning(f"Chapter {CurrentChapter.id} is empty.")

		self._SystemObjects.logger.amending_end(AmendedChaptersCount)

	def download_images(self):
		"""Скачивает изображения из данных тайтла."""

		if self.covers: self._DownloadCovers()
		if self._Persons: self._DownloadPersonsImages()

	def open(self, identificator: int | str, selector_type: By = By.Filename):
		"""
		Открывает локальный JSON файл и интерпретирует его данные.

		:param identificator: Идентификатор тайтла: ID или алиас.
		:type identificator: int | str
		:param selector_type: Режим поиска файла. По умолчанию `By.Filename` – идентификатор соответствует имени файла без расширения.
		:type selector_type: By
		:raises FileNotFoundError: Не удалось найти файл с указанным именем.
		:raises JSONDecodeError: Ошибка десериализации JSON.
		:raises UnsupportedFormat: Неподдерживаемый формат JSON.
		"""

		Data = None
		Directory = self._ParserSettings.common.titles_directory

		match selector_type:

			case By.Filename:
				Path = f"{Directory}/{identificator}.json"
				Data = SafelyReadTitleJSON(f"{Directory}/{identificator}.json")

			case By.Slug:
			
				if self._ParserSettings.common.use_id_as_filename and self._SystemObjects.CACHING:
					ID = self._SystemObjects.temper.shared_data.journal.get_id_by_slug(identificator)

					if ID:
						PathBuffer = f"{Directory}/{ID}.json"
						if os.path.exists(PathBuffer): Data = SafelyReadTitleJSON(PathBuffer)

				else:
					Path = f"{Directory}/{identificator}.json"
					if os.path.exists(Path): Data = SafelyReadTitleJSON(f"{Directory}/{identificator}.json")
				
				if not Data: Data = self._SearchFileInDirectory(Directory, identificator, By.Slug)

			case By.ID:
				
				if self._ParserSettings.common.use_id_as_filename:
					Path = f"{Directory}/{identificator}.json"
					if os.path.exists(Path): Data = SafelyReadTitleJSON(f"{Directory}/{identificator}.json")

				elif self._SystemObjects.CACHING:
					Slug = self._SystemObjects.temper.shared_data.journal.get_slug_by_id(identificator)

					if Slug:
						PathBuffer = f"{Directory}/{Slug}.json"
						if os.path.exists(PathBuffer): Data = SafelyReadTitleJSON(PathBuffer)

				if not Data: Data = self._SearchFileInDirectory(Directory, identificator, By.ID)

		if Data:
			self._Title = Data
			self._SetUsedFilename(str(self.id) if self._ParserSettings.common.use_id_as_filename else self.slug)

		else: raise FileNotFoundError()

		if self.content_language: self._WordsDictionary = GetDictionaryPreset(self.content_language)
		self._ParseBranchesToObjects()

	def parse(self, index: int = 0, titles_count: int = 1):
		"""
		Получает основные данные тайтла.
			index – индекс текущего тайтла;\n
			titles_count – количество тайтлов в задаче.
		"""
	
		self._SystemObjects.logger.parsing_start(self, index, titles_count)

		self.set_site(self._Parser.manifest.site)
		self._Parser.parse()

	def repair(self, chapter_id: int):
		"""
		Восстанавливает содержимое главы, заново получая его из источника.

		:param chapter_id: Уникальный идентификатор целевой главы.
		:type chapter_id: int
		:raises ChapterNotFound: Выбрасывается, если в локальном JSON не найдена глава с указанным ID.
		"""

		SearchResult = self._FindChapterByID(chapter_id)
		if not SearchResult: raise Exceptions.ChapterNotFound(chapter_id)

		BranchData: "BaseBranch" = SearchResult.branch
		ChapterData: "MangaChapter | RanobeChapter" = SearchResult.chapter
		
		ChapterData.clear()
		self._Parser.amend(BranchData, ChapterData)
		
		if self.format == "melon-manga" and ChapterData.slides or self.format == "melon-ranobe" and ChapterData.paragraphs:
			self._SystemObjects.logger.chapter_repaired(ChapterData)

	def save(self, sorting: bool = False):
		"""
		Сохраняет данные тайтла в локальный файл JSON.

		:param sorting: Указывает, нужно ли провести сортировку глав на основе их нумерации.
		:type sorting: bool
		"""

		self._UpdatePersons()
		self._UpdateContent(sorting = sorting)
		self._UpdateBranchesInfo()
		self._Parser.postprocessor()
		WriteJSON(self._TitlePath, self._Title)

		if self._SystemObjects.CACHING and all((self.id, self.slug)): self._SystemObjects.temper.shared_data.journal.update(self.id, self.slug)
		self._SystemObjects.logger.info("Saved.")
			
	def set_parser(self, parser: "BaseParser"):
		"""
		Задаёт парсер для вызова методов наполнения контентом.

		:param parser: Парсер.
		:type parser: BaseParser
		"""

		parser.set_title(self)
		self._Parser = parser

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ УСТАНОВКИ СВОЙСТВ <<<<< #
	#==========================================================================================#

	def add_another_name(self, another_name: str):
		"""
		Добавляет альтернативное название.
			another_name – название.
		"""
		
		if another_name != self._Title["localized_name"] and another_name != self._Title["eng_name"] and another_name: self._Title["another_names"].append(another_name)

	def add_cover(self, link: str, filename: str | None = None, width: int | None = None, height: int | None = None):
		"""
		Добавляет обложку.
			link – ссылка на изображение;\n
			filename – имя локального файла;\n
			width – ширина обложки;\n
			height – высота обложки.
		"""

		if not filename: filename = link.split("/")[-1]
		CoverInfo = {
			"link": link,
			"filename": filename,
			"width": width,
			"height": height
		}

		if not self._ParserSettings.common.sizing_images: 
			del CoverInfo["width"]
			del CoverInfo["height"]

		if link not in tuple(CoverData["link"] for CoverData in self.covers): self._Title["covers"].append(CoverInfo)

	def add_author(self, author: str):
		"""
		Добавляет автора.
			author – автор.
		"""

		if author and author not in self._Title["authors"]: self._Title["authors"].append(author)

	def add_genre(self, genre: str):
		"""
		Добавляет жанр.
			genre – жанр.
		"""

		if genre not in self._Title["genres"]: self._Title["genres"].append(genre)

	def add_tag(self, tag: str):
		"""
		Добавляет тег.
			tag – тег.
		"""

		if tag not in self._Title["tags"]: self._Title["tags"].append(tag)

	def add_franshise(self, franshise: str):
		"""
		Добавляет франшизу.
			franshise – франшиза.
		"""

		if franshise not in self._Title["franshises"]: self._Title["franshises"].append(franshise)

	def add_person(self, person: Person):
		"""
		Добавляет персонажа.
			person – данные персонажа.
		"""
		
		if person not in self._Persons: self._Persons.append(person)

	def add_branch(self, branch: BaseBranch):
		"""
		Добавляет ветвь. Одинаковые объекты или ветви с повторяющимся ID будут проигнорированы.

		:param branch: Ветвь контента.
		:type branch: BaseBranch
		:raises ParsingError: Выбрасывается при отсутствии у добавляемой ветви ID.
		"""

		if branch.id == None: raise Exceptions.ParsingError("Branch must have unique ID.")
		if branch.id in tuple(Element.id for Element in self._Branches): return
		self._Branches.append(branch)
		self._Branches = sorted(self._Branches, key = lambda Value: Value.chapters_count, reverse = True)

	def set_site(self, site: str):
		"""
		Задаёт домен источника.
			site – домен сайта.
		"""

		self._Title["site"] = site

	def set_id(self, id: int):
		"""
		Задаёт целочисленный уникальный идентификатор тайтла.
			id – идентификатор.
		"""

		self._Title["id"] = id
		if not self.slug: self.set_slug(self._SystemObjects.temper.shared_data.journal.get_slug_by_id(id))
		if self._ParserSettings.common.use_id_as_filename: self._SetUsedFilename(id)

	def set_slug(self, slug: str):
		"""
		Задаёт алиас манги.
			slug – алиас.
		"""

		self._Title["slug"] = slug
		if not self.id: self.set_id(self._SystemObjects.temper.shared_data.journal.get_id_by_slug(slug))
		if not self._ParserSettings.common.use_id_as_filename: self._SetUsedFilename(slug)

	def set_content_language(self, language_code: str | None) -> WordsDictionary | None:
		"""
		Задаёт язык контента по стандарту ISO 639-3.

		:param original_language: Код языка.
		:type original_language: str | None
		:raise ValueError: Выбрасывается при несоответствии кода языка стандарту.
		:return: Словарь ключевых слов для выбранного языка, если доступен.
		:rtype: WordsDictionary | None
		"""

		if language_code: CheckLanguageCode(language_code)
		self._Title["content_language"] = language_code
		self._WordsDictionary = GetDictionaryPreset(self.content_language)

		return self._WordsDictionary

	def set_localized_name(self, localized_name: str | None):
		"""
		Задаёт главное название манги на русском.
			ru_name – название на русском.
		"""

		self._Title["localized_name"] = localized_name.strip() if localized_name else None

	def set_eng_name(self, eng_name: str | None):
		"""
		Задаёт главное название манги на английском.
			en_name – название на английском.
		"""

		self._Title["eng_name"] = eng_name.strip() if eng_name else None

	def set_another_names(self, another_names: list[str]):
		"""
		Задаёт список альтернативных названий на любых языках.
			another_names – список названий.
		"""

		self._Title["another_names"] = self._CheckStringsList(another_names)

	def set_covers(self, covers: list[dict]):
		"""
		Задаёт список описаний обложек.
			covers – список названий.
		"""

		self._Title["covers"] = covers

	def set_authors(self, authors: list[str]):
		"""
		Задаёт список авторов.
			covers – список авторов.
		"""

		self._Title["authors"] = self._CheckStringsList(authors)

	def set_publication_year(self, publication_year: int | None):
		"""
		Задаёт год публикации тайтла.

		:param publication_year: Год публикации.
		:type publication_year: int | None
		"""

		self._Title["publication_year"] = int(publication_year) if publication_year else None

	def set_description(self, description: str | None):
		"""
		Задаёт описание тайтла.

		:param description: Описание тайтла.
		:type description: str | None
		"""

		self._Title["description"] = Zerotify(description) if not description else description.strip()

	def set_age_limit(self, age_limit: int | None):
		"""
		Задаёт возрастной рейтинг.
			age_limit – возрастной рейтинг.
		"""

		self._Title["age_limit"] = age_limit

	def set_genres(self, genres: list[str]):
		"""
		Задаёт список жанров.
			genres – список жанров.
		"""

		self._Title["genres"] = self._CheckStringsList(genres)

	def set_tags(self, tags: list[str]):
		"""
		Задаёт список тегов.
			tags – список тегов.
		"""

		self._Title["tags"] = self._CheckStringsList(tags)

	def set_franchises(self, franchises: list[str]):
		"""
		Задаёт список франшиз.
			franchises – список франшиз.
		"""

		self._Title["franchises"] = self._CheckStringsList(franchises)

	def set_persons(self, persons: list[Person]):
		"""
		Задаёт персонажей.
			person – список персонажей.
		"""
		
		for CurrentPerson in persons: self.add_person(CurrentPerson)

	def set_status(self, status: Statuses | None):
		"""
		Задаёт статус манги.
			status – статус.
		"""

		if status: self._Title["status"] = status.value
		else: self._Title["status"] = None
	
	def set_is_licensed(self, is_licensed: bool | None):
		"""
		Задаёт статус лицензирования манги.
			is_licensed – статус лицензирования.
		"""

		self._Title["is_licensed"] = is_licensed