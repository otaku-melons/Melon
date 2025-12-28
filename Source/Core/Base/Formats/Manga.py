from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseBranch, BaseTitle
from Source.Core.Exceptions import ChapterNotFound

from dublib.Methods.Filesystem import ReadJSON

from typing import TYPE_CHECKING
import enum
import os

if TYPE_CHECKING:
	from Source.Core.SystemObjects import SystemObjects

#==========================================================================================#
# >>>>> ПЕРЕЧИСЛЕНИЯ ТИПОВ <<<<< #
#==========================================================================================#

class Types(enum.Enum):
	"""Определения типов манги."""

	manga = "manga"
	manhwa = "manhwa"
	manhua = "manhua"
	oel = "oel"
	western_comic = "western_comic"
	russian_comic = "russian_comic"
	indonesian_comic = "indonesian_comic"

#==========================================================================================#
# >>>>> ДОПОЛНИТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class Chapter(BaseChapter):
	"""Глава манги."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def slides(self) -> list[dict]:
		"""Список слайдов."""

		return self._Chapter["slides"]
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Глава манги.
			system_objects – коллекция системных объектов.
		"""

		self._SystemObjects = system_objects

		self._Chapter = {
			"id": None,
			"slug": None,
			"volume": None,
			"number": None,
			"name": None,
			"is_paid": None,
			"workers": [],
			"slides": []	
		}

		self._SetParagraphsMethod = self._Pass
		self._SetSlidesMethod = self.set_slides

	def add_slide(self, link: str, width: int | None = None, height: int | None = None):
		"""
		Добавляет данные о слайде.
			link – ссылка на слайд;\n
			width – ширина слайда;\n
			height – высота слайда.
		"""

		ParserSettings = self._SystemObjects.manager.current_parser_settings
		SlideInfo = {
			"index": len(self._Chapter["slides"]) + 1,
			"link": link,
			"width": width,
			"height": height
		}

		if width and height and ParserSettings.filters.image.check_sizes(width, height):
			return

		if not ParserSettings.common.sizing_images: 
			del SlideInfo["width"]
			del SlideInfo["height"]

		self._Chapter["slides"].append(SlideInfo)

	def clear_slides(self):
		"""Удаляет данные слайдов."""

		self._Chapter["slides"] = list()

	def set_slides(self, slides: list[dict]):
		"""
		Задаёт список слайдов.
			slides – список словарей, описывающих слайды.
		"""

		for Slide in slides:
			Link = Slide["link"]
			Width = Slide["width"] if "width" in Slide.keys() else None
			Height = Slide["height"] if "height" in Slide.keys() else None

			self.add_slide(Link, Width, Height)

class Branch(BaseBranch):
	"""Ветвь."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def chapters(self) -> list[Chapter]:
		"""Список глав."""

		return self._Chapters
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, id: int):
		"""
		Ветвь.
			ID – уникальный идентификатор ветви.
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self._ID = id
		self._Chapters: list[Chapter] = list()

	def add_chapter(self, chapter: Chapter):
		"""
		Добавляет главу в ветвь.
			chapter – глава.
		"""

		self._Chapters.append(chapter)

	def get_chapter_by_id(self, id: int) -> Chapter:
		"""
		Возвращает главу по её уникальному идентификатору.
			id – идентификатор главы.
		"""

		Data = None

		for CurrentChapter in self._Chapters:
			if CurrentChapter.id == id: Data = CurrentChapter

		if not Data: raise KeyError(id)

		return CurrentChapter
	
	def replace_chapter_by_id(self, chapter: Chapter, id: int):
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

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Manga(BaseTitle):
	"""Манга."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def type(self) -> Types | None:
		"""Тип тайтла."""

		return self._Title["type"]

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _ParseBranchesToObjects(self):
		"""Преобразует данные ветвей в объекты."""

		Branches = list()

		for BranchID in self._Title["content"]:
			BufferBranch = Branch(int(BranchID))

			for CurrentChapter in self._Title["content"][BranchID]:
				BufferChapter = Chapter(self._SystemObjects)
				BufferChapter.set_dict(CurrentChapter)
				BufferBranch.add_chapter(BufferChapter)

			Branches.append(BufferBranch)

		self._Branches = Branches

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		self._Title = {
			"format": "melon-manga",
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

			"type": None,
			"status": None,
			"is_licensed": None,
			
			"genres": [],
			"tags": [],
			"franchises": [],
			"persons": [],
			
			"branches": [],
			"content": {} 
		}

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def merge(self):
		"""Объединяет данные описательного файла и текущей структуры данных."""
		
		Path = f"{self._ParserSettings.common.titles_directory}/{self._UsedFilename}.json"
		
		if os.path.exists(Path) and not self._SystemObjects.FORCE_MODE:
			LocalManga = ReadJSON(Path)
			LocalContent = dict()
			MergedChaptersCount = 0

			if LocalManga["format"] != "melon-manga":
				self._SystemObjects.logger.unsupported_format(self)
				return
			
			for BranchID in LocalManga["content"]:
				for CurrentChapter in LocalManga["content"][BranchID]: LocalContent[CurrentChapter["id"]] = CurrentChapter["slides"]
			
			for BranchID in self._Title["content"]:
		
				for ChapterIndex in range(len(self._Title["content"][BranchID])):
				
					if self._Title["content"][BranchID][ChapterIndex]["id"] in LocalContent.keys():
						ChapterID = self._Title["content"][BranchID][ChapterIndex]["id"]

						if LocalContent[ChapterID]:
							self._Title["content"][BranchID][ChapterIndex]["slides"] = LocalContent[ChapterID]
							MergedChaptersCount += 1

			self._SystemObjects.logger.merging_end(self, MergedChaptersCount)

		self._Branches = list()

		for CurrentBranchID in self._Title["content"].keys():
			BranchID = int(CurrentBranchID)
			NewBranch = Branch(BranchID)

			for ChapterData in self._Title["content"][CurrentBranchID]:
				NewChapter = Chapter(self._SystemObjects)
				NewChapter.set_dict(ChapterData)
				NewBranch.add_chapter(NewChapter)

			self.add_branch(NewBranch)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ УСТАНОВКИ СВОЙСТВ <<<<< #
	#==========================================================================================#

	def set_type(self, type: Types | None):
		"""
		Задаёт типп манги.
			type – тип.
		"""

		if type: self._Title["type"] = type.value
		else: self._Title["type"] = None