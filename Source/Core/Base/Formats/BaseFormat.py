from Source.Core.Base.Formats.Components.Structs import *
from Source.Core.Exceptions import UnsupportedFormat
from Source.Core.Timer import Timer

from dublib.Methods.Filesystem import ListDir, ReadJSON, WriteJSON
from dublib.Methods.Data import Zerotify

from typing import Any, Iterable, TYPE_CHECKING
from time import sleep
import os

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.BaseParser import BaseParser
	from Source.Core.SystemObjects import SystemObjects

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

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

	def to_dict(self, remove_sizes: bool = False) -> dict:
		"""
		Возвращает словарное представление данных персонажа.
			remove_sizes – указывает, нужно ли удалить ключи размеров изображений.
		"""

		Data = self.__Data.copy()

		if remove_sizes:

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

	def __init__(self):
		"""Базовая глава."""

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

	def remove_extra_data(self, key: str):
		"""
		Удаляет дополнительные данные главы.

		:param key: Ключ, под которым хранятся дополнительные данные.
		:type key: str
		"""

		try: del self._Chapter[key]
		except KeyError: pass

	def set_dict(self, dictionary: dict):
		"""
		Перебирает ключи в переданном словаре для автоматической подстановки значений в поля данных главы.
			dictionary – словарь данных главы.
		"""
		
		dictionary = dictionary.copy()
		KeyMethods = {
			"id": self.set_id,
			"volume": self.set_volume,
			"name": self.set_name,
			"is_paid": self.set_is_paid,
			"workers": self.set_workers,
			"slides": self._SetSlidesMethod,
			"paragraphs": self._SetParagraphsMethod
		}

		for Key in KeyMethods.keys():
			
			if Key in dictionary.keys():
				Value = dictionary[Key]
				KeyMethods[Key](Value)
				del dictionary[Key]

		for Key in dictionary.keys():
			Value = dictionary[Key]
			self.add_extra_data(Key, Value)

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
			name – название главы.
		"""

		self._Chapter["name"] = Zerotify(name)

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
			ID – уникальный идентификатор ветви.
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self._ID = id
		self._Chapters: list[BaseChapter] = list()

	def add_chapter(self, chapter: BaseChapter):
		"""
		Добавляет главу в ветвь.
			chapter – глава.
		"""

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
	def used_filename(self) -> str | None:
		"""Используемое имя файла."""

		return self._UsedFilename

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
	def slug(self) -> int | None:
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
			if CoverIndex == 2: Link = "https://renovels.org/media/titles/i-was-an-economist-and-then-i-became-demon-emperor/cover_fd3e4f3885.webp"
			Filename = self._Title["covers"][CoverIndex]["filename"]
			IsExists = self._Parser.images_downloader.is_exists(Link, CoversDirectory, Filename)
			print(f"Downloading cover: \"{Filename}\"... ", end = "", flush = True)

			if IsExists and not self._SystemObjects.FORCE_MODE:
				print("Already exists.")
				continue

			Result = self._Parser.image(Link)
			
			if Result.code == 200:
				self._Parser.images_downloader.move_from_temp(CoversDirectory, Result.value, Filename)
				if IsExists: print("Overwritten.")
				else: print("Done.")
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
				print(f"Downloading person image: \"{Filename}\"... ", end = "", flush = True)
				
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

	def _FindChapterByID(self, chapter_id: int) -> tuple[BaseBranch, BaseChapter] | None:
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

		Result = (BranchResult, ChapterResult) if ChapterResult else None

		return Result

	def _SafeRead(self, path: str) -> dict:
		"""
		В случае ошибки декодирования JSON выбрасывает исключение.

		:param path: Путь к JSON файлу.
		:type path: str
		:raises JSONDecodeError: Ошибка десериализации JSON.
		:raises UnsupportedFormat: Неподдерживаемый формат JSON.
		:return: Словарное представление JSON тайтла.
		:rtype: dict
		"""

		Formats: tuple[str] = tuple(File[:-3] for File in ListDir("Docs/Examples"))
		Data = ReadJSON(path)
		if "format" not in Data.keys(): raise UnsupportedFormat()
		elif Data["format"] not in Formats: raise UnsupportedFormat(Data["format"])

		return Data
	
	def _UpdateBranchesInfo(self):
		"""Обновляет информацию о ветвях."""

		Branches = list()
		for CurrentBranch in self._Branches: Branches.append({"id": CurrentBranch.id, "chapters_count": CurrentBranch.chapters_count})
		self._Title["branches"] = sorted(Branches, key = lambda Value: Value["chapters_count"], reverse = True) 

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
		self._UsedFilename = None
		self._Parser: "BaseParser" = None
		self._Timer = None
		
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

	def __getitem__(self, key: str) -> Any:
		"""
		Возвращает значение из внутреннего словаря.

		:param key: Ключ.
		:type key: str
		:return: Значение.
		:rtype: Any
		"""

		return self._Title[key]
	
	def __setitem__(self, key: str, value: Any):
		"""
		Задаёт значение для внутреннего словаря.

		:param key: Ключ.
		:type key: str
		:param value: Значение.
		:type value: Any
		"""

		self._Title[key] = value

	def amend(self):
		"""Дополняет контент содержимым."""

		AmendedChaptersCount = 0
		ProgressIndex = 0

		for CurrentBranch in self._Branches:

			for CurrentChapter in CurrentBranch.chapters:
				ChapterContent = list()
				if self.format == "melon-manga": ChapterContent = CurrentChapter.slides
				elif self.format == "melon-ranobe": ChapterContent = CurrentChapter.paragraphs

				if not ChapterContent:
					ProgressIndex += 1
					self._Parser.amend(CurrentBranch, CurrentChapter)

					if ChapterContent:
						AmendedChaptersCount += 1
						self._SystemObjects.logger.chapter_amended(self, CurrentChapter)
						sleep(self._ParserSettings.common.delay)

				self._Parser.amend_postprocessor(CurrentChapter)

		self._SystemObjects.logger.amending_end(self, AmendedChaptersCount)

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

		if selector_type == By.Filename:
			Path = f"{Directory}/{identificator}.json"
			if os.path.exists(Path): Data = self._SafeRead(f"{Directory}/{identificator}.json")

		if selector_type == By.Slug:
		
			if self._ParserSettings.common.use_id_as_filename and self._SystemObjects.CACHING_ENABLED:
				ID = self._SystemObjects.temper.shared_data.journal.get_id_by_slug(identificator)

				if ID:
					PathBuffer = f"{Directory}/{ID}.json"
					if os.path.exists(PathBuffer): Data = self._SafeRead(PathBuffer)

			else:
				Path = f"{Directory}/{identificator}.json"
				if os.path.exists(Path): Data = self._SafeRead(f"{Directory}/{identificator}.json")
				
			if not Data:
				LocalTitles = ListDir(Directory)
				LocalTitles = tuple(filter(lambda File: File.endswith(".json"), LocalTitles))

				for File in LocalTitles:
					Path = f"{Directory}/{File}"

					if os.path.exists(Path):
						Buffer = self._SafeRead(Path)

						if Buffer["slug"] == identificator:
							Data = Buffer
							break

		if selector_type == By.ID:
			
			if self._ParserSettings.common.use_id_as_filename:
				Path = f"{Directory}/{identificator}.json"
				if os.path.exists(Path): Data = self._SafeRead(f"{Directory}/{identificator}.json")

			elif self._SystemObjects.CACHING_ENABLED:
				Slug = self._SystemObjects.temper.shared_data.journal.get_slug_by_id(identificator)

				if Slug:
					PathBuffer = f"{Directory}/{Slug}.json"
					if os.path.exists(PathBuffer): Data = self._SafeRead(PathBuffer)

			if not Data:
				LocalTitles = ListDir(Directory)
				LocalTitles = tuple(filter(lambda File: File.endswith(".json"), LocalTitles))

				for File in LocalTitles:
					Path = f"{Directory}/{File}"

					if os.path.exists(Path):
						Buffer = self._SafeRead(Path)

						if Buffer["id"] == identificator:
							Data = Buffer
							break

		if Data:
			self._Title = Data
			if self._SystemObjects.CACHING_ENABLED: self._SystemObjects.temper.shared_data.journal.update(self.id, self.slug)
			self._UsedFilename = str(self.id) if self._ParserSettings.common.use_id_as_filename else self.slug

		else: raise FileNotFoundError()

		self._ParseBranchesToObjects()

	def parse(self, index: int = 0, titles_count: int = 1):
		"""
		Получает основные данные тайтла.
			index – индекс текущего тайтла;\n
			titles_count – количество тайтлов в задаче.
		"""

		self._Timer = Timer()
		self._Timer.start()
		self._SystemObjects.logger.parsing_start(self, index, titles_count)

		self.set_site(self._Parser.manifest.site)
		self._Parser.parse()
		self._UsedFilename = str(self.id) if self._ParserSettings.common.use_id_as_filename else self.slug

	def save(self, end_timer: bool = False):
		"""
		Сохраняет данные тайтла.
			end_timer – указывает, нужно ли остановить таймер и вывести затраченное время.
		"""

		try:
			for BranchID in self._Title["content"]:
				self._Title["content"][BranchID] = sorted(
					self._Title["content"][BranchID],
					key = lambda Value: (
						list(map(int, Value["volume"].split(".") if Value["volume"] else "")),
						list(map(int, Value["number"].split(".") if Value["number"] else ""))
					)
				)

		except: self._SystemObjects.logger.warning(f"Title: \"{self.slug}\" (ID: {self.id}). Error occurs during sorting chapters.")

		self._Title["persons"] = list()
		for CurrentPerson in self._Persons: self._Title["persons"].append(CurrentPerson.to_dict(not self._ParserSettings.common.sizing_images))

		WriteJSON(f"{self._ParserSettings.common.titles_directory}/{self._UsedFilename}.json", self._Title)
		self._SystemObjects.temper.shared_data.journal.update(self.id, self.slug)
		self._SystemObjects.logger.info("Saved.")

		if end_timer: 
			ElapsedTime = self._Timer.ends()
			self._Timer = None
			print(f"Done in {ElapsedTime}.")
			
	def set_parser(self, parser: Any):
		"""Задаёт парсер для вызова методов."""

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
		Добавляет ветвь.
			branch – ветвь.
		"""

		if branch not in self._Branches: self._Branches.append(branch)
		for CurrentBranch in self._Branches: self._Title["content"][str(CurrentBranch.id)] = CurrentBranch.to_list()
		self._UpdateBranchesInfo()

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

	def set_slug(self, slug: str):
		"""
		Задаёт алиас манги.
			slug – алиас.
		"""

		self._Title["slug"] = slug

	def set_content_language(self, content_language: str | None):
		"""
		Задаёт язык контента по стандарту ISO 639-3.
			content_language – код языка.
		"""

		if type(content_language) == str and len(content_language) != 3: raise TypeError(content_language)
		self._Title["content_language"] = content_language.lower() if content_language else None

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