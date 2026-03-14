from .Elements import Blockquote, Header, Image, Paragraph
from .Enums import ChaptersTypes

from ..Components.WordsDictionary import CheckLanguageCode

from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseBranch, BaseTitle
from Source.Core import Exceptions

from dublib.Methods.Filesystem import ReadJSON

from typing import Iterable, TYPE_CHECKING
import os

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.RanobeParser import RanobeParser
	from Source.Core.SystemObjects import SystemObjects

#==========================================================================================#
# >>>>> ВНУТРЕННИЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class Chapter(BaseChapter):
	"""Глава ранобэ."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def footnotes(self) -> tuple[str]:
		"""Последовательность заметок."""

		return tuple(self._Chapter["footnotes"])

	@property
	def paragraphs(self) -> tuple[str]:
		"""Последовательность абзацев."""

		return tuple(self._Chapter["paragraphs"])
	
	@property
	def type(self) -> ChaptersTypes | None:
		"""Тип главы."""

		return ChaptersTypes[self._Chapter["type"]]

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", title: "Ranobe"):
		"""
		Глава ранобэ.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param title: Данные тайтла.
		:type title: Ranobe
		"""

		self._SystemObjects = system_objects
		self._Title = title

		self._ParserSettings = system_objects.controller.current_parser_settings
		self._Chapter = {
			"id": None,
			"slug": None,
			"volume": None,
			"number": None,
			"name": None,
			"type": None,
			"is_paid": None,
			"workers": [],
			"paragraphs": [],
			"footnotes": []
		}

	def add_element(self, element: "Paragraph | Image | Header | Blockquote"):
		"""
		Добавляет элемент в главу.

		:param element: Элемент главы.
		:type element: Paragraph | Image | Header | Blockquote
		:raise TypeError: Выбрасывается при передаче неподдерживаемого элемента.
		"""

		if type(element) not in (Paragraph, Image, Header, Blockquote): raise TypeError("Unsupported element.")

		if type(element) in (Paragraph, Blockquote, Header):
			self._Chapter["paragraphs"].append(element.to_html(footnotes_offset = len(self.footnotes)))
			for CurrentNote in element.footnotes: self._Chapter["footnotes"].append(CurrentNote.to_html())

		else: self._Chapter["paragraphs"].append(element.to_html())

	def set_elements(self, elements: "Iterable[Paragraph | Image | Header | Blockquote]"):
		"""
		Задаёт набор элементов главы.

		:param elements: Набор элементов главы.
		:type elements: Iterable[Paragraph | Image | Header | Blockquote]
		"""

		for Element in elements: self.add_element(Element)

	def set_type(self, type: ChaptersTypes | None):
		"""
		Задаёт тип главы.
			type – тип.
		"""

		if type: self._Chapter["type"] = type.value
		else: self._Chapter["type"] = None

class Branch(BaseBranch):
	"""Ветвь."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def chapters(self) -> tuple[Chapter]:
		"""Последовательность глав."""

		return super().chapters
	
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
		Добавляет главу в ветвь. Если глава с таким ID уже существует, добавление не происходит.

		:param chapter: Данные главы.
		:type chapter: Chapter
		:raises ParsingError: Выбрасывается при отсутствии у добавляемой главы ID.
		"""

		super().add_chapter(chapter)

	def get_chapter_by_id(self, id: int) -> Chapter:
		"""
		Возвращает главу по её уникальному идентификатору.

		:param id: ID главы.
		:type id: int
		:raises KeyError: Выбрасывается при отсутствии главы в ветви.
		:return: Глава.
		:rtype: Chapter
		"""

		return super().get_chapter_by_id(id)

	def replace_chapter_by_id(self, chapter: Chapter, id: int):
		"""
		Заменяет главу в ветви по её ID.

		:param chapter: Новая глава.
		:type chapter: Chapter
		:param id: ID заменяемой главы.
		:type id: int
		:raises KeyError: Выбрасывается при отсутствии заменяемой главы в ветви.
		"""

		super().replace_chapter_by_id(chapter, id)

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Ranobe(BaseTitle):
	"""Ранобэ."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def parser(self) -> "RanobeParser":
		"""Установленный парсер контента."""

		return self._Parser

	#==========================================================================================#
	# >>>>> СВОЙСТВА ТАЙТЛА <<<<< #
	#==========================================================================================#

	@property
	def original_language(self) -> str | None:
		"""Оригинальный язык контента по стандарту ISO 639-3."""

		return self._Title["original_language"]
	
	@property
	def branches(self) -> tuple[Branch]:
		"""Последовательность ветвей тайтла."""

		return super().branches

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _ParseBranchesToObjects(self):
		"""Преобразует данные ветвей в объекты."""

		Branches = list()

		for BranchID in self._Title["content"]:
			BufferBranch = Branch(int(BranchID))

			for CurrentChapter in self._Title["content"][BranchID]:
				BufferChapter = Chapter(self._SystemObjects, self)
				BufferChapter.set_dict(CurrentChapter)
				BufferBranch.add_chapter(BufferChapter)

			Branches.append(BufferBranch)

		self._Branches = Branches

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		self._Title = {
			"format": "melon-ranobe",
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

			"original_language": None,
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
		"""Выполняет слияние содержимого описанных локально глав с текущей структурой."""

		MergedChaptersCount = 0

		if os.path.exists(self._TitlePath):
			LocalData = ReadJSON(self._TitlePath)
		
			if LocalData.get("format") != "melon-ranobe":
				self._SystemObjects.logger.unsupported_format(LocalData.get("format"))
				return
			
			for BranchID in LocalData["content"]:
				for CurrentChapter in LocalData["content"][BranchID]:
					CurrentChapter: dict

					Paragraphs = CurrentChapter.get("paragraphs")
					if not Paragraphs: continue

					ChapterID = CurrentChapter.get("id")
					if not ChapterID: raise Exceptions.MergingError()

					SearchResult = self._FindChapterByID(ChapterID)
					if not SearchResult: continue
					Container: Chapter = SearchResult.chapter
					Container["paragraphs"] = Paragraphs
					MergedChaptersCount += 1
	
			self._SystemObjects.logger.merging_end(MergedChaptersCount)

	#==========================================================================================#
	# >>>>> МЕТОДЫ УСТАНОВКИ СВОЙСТВ <<<<< #
	#==========================================================================================#

	def set_original_language(self, language_code: str | None):
		"""
		Задаёт оригинальный язык контента по стандарту ISO 639-3.

		:param language_code: Код языка.
		:type language_code: str | None
		:raise ValueError: Выбрасывается при несоответствии кода языка стандарту.
		"""

		if language_code: CheckLanguageCode(language_code)
		self._Title["original_language"] = language_code.lower() if language_code else None