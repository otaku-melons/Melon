from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseBranch, BaseTitle
from Source.Core.Base.Parsers.Components.ImagesDownloader import ImagesDownloader
from Source.Core.Exceptions import ChapterNotFound, UnresolvedTag

from dublib.Methods.Data import RemoveRecurringSubstrings
from dublib.Methods.Filesystem import ReadJSON
from dublib.Polyglot import HTML
from bs4 import BeautifulSoup
from time import sleep

from typing import TYPE_CHECKING
from pathlib import Path
import enum
import os

if TYPE_CHECKING:
	from Source.Core.SystemObjects import SystemObjects

#==========================================================================================#
# >>>>> ПЕРЕЧИСЛЕНИЯ ТИПОВ <<<<< #
#==========================================================================================#

class ChaptersTypes(enum.Enum):
	"""Определения типов глав."""

	afterword = "afterword"
	art = "art"
	chapter = "chapter"
	epilogue = "epilogue"
	extra = "extra"
	glossary = "glossary"
	prologue = "prologue"
	trash = "trash"

#==========================================================================================#
# >>>>> ДОПОЛНИТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class Chapter(BaseChapter):
	"""Глава ранобэ."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def paragraphs(self) -> list[str]:
		"""Список абзацев."""

		return self._Chapter["paragraphs"]
	
	@property
	def type(self) -> ChaptersTypes | None:
		"""Тип главы."""

		return ChaptersTypes[self._Chapter["type"]]

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __DownloadImages(self, paragraph: str) -> str:
		"""
		Скачивает иллюстрации из абзаца.

		:param paragraph: Абзац текста.
		:type paragraph: str
		:return: Параграф с заменённым путями изображений в тегах `img`.
		:rtype: str
		"""

		Parser = self.__Title.parser
		Soup = BeautifulSoup(paragraph, "html.parser")
		Images = Soup.find_all("img")
		
		for Image in Images:
			Image: BeautifulSoup
			Message = "Done."
			
			if Image.has_attr("src"):
				Link = Image["src"]
				Filename = Link.split("/")[-1].split("?")[0]
				Result = None

				Directory = f"{Parser.settings.common.images_directory}/{self.__Title.used_filename}/illustrations/{self.id}"
				ImageTagSource = Path(f"{Directory}/{Filename}")
				ImageTagSource = Path(*ImageTagSource.parts[1:]).as_posix()
				if ImageTagSource == Link: continue

				print(f"Downloading image: \"{Filename}\"... ", end = "")
				Status = Parser.image(Link)
				if Status.has_errors: continue
				if not Status["exists"]: sleep(Parser.settings.common.delay)
				Filename = Status.value

				if Filename: 
					TempPath = f"{self._SystemObjects.temper.parser_temp}/{Filename}"
					Image.attrs = {"src": ImageTagSource}

					if Parser.settings.filters.image.check_hash(TempPath):
						Message = "Filtered by MD5 hash."
						Image.decompose()
						os.remove(TempPath)

					else:
						if not os.path.exists(Directory): os.makedirs(Directory)
						Result = Parser.images_downloader.move_from_temp(Directory, Filename)

						if Result.value and Result["exists"]:
							if self._SystemObjects.FORCE_MODE: Message = "Overwritten."
							else: Message = "Already exists."

					print(Message)

			else: 
				self._SystemObjects.logger.warning("Image decomposed because has not source.")
				Image.decompose()

		return str(Soup)

	def __GetLocalizedChapterWord(self) -> str | None:
		"""Возвращает слово в нижнем регистре, обозначающее главу."""

		Language = self.__Title.content_language
		Words = {
			None: None,
			"rus": "глава",
			"eng": "chapter"
		}
		Word = None
		if Language in Words.keys(): Word = Words[Language]

		return Word

	def __MergeSimilarTags(self, soup: BeautifulSoup, tag: str) -> BeautifulSoup:
		"""
		Объединяет рядом располагающиеся одинаковые теги, отдлённые пробельными символами.

		:param soup: Обрабатываемый абзац текста.
		:type soup: BeautifulSoup
		:param tag: Имя тега.
		:type tag: str
		:return: Обработанный абзац текста.
		:rtype: BeautifulSoup
		"""


		MergableTags = soup.find_all(tag)
		if not MergableTags: return soup
		NewText = ""

		for Index, Tag in enumerate(MergableTags):
			NewText += Tag.get_text()
			
			if Index + 1 < len(MergableTags):
				BetweenText = Tag.next_sibling.string
				# Сохранение пробельных символов между тегами.
				if BetweenText: NewText += BetweenText

		NewTag = soup.new_tag(tag)
		NewTag.string = NewText
		MergableTags[0].insert_before(NewTag)
		for Tag in MergableTags: Tag.extract()

		return soup

	def __TryGetName(self, paragraph: str):
		"""
		Пытается получить название главы из абзаца.
			paragraph – абзац.
		"""

		if not self.name:
			LocalizedChapterWord = self.__GetLocalizedChapterWord()
			ChapterCounterLength = len(f"{LocalizedChapterWord} {self.number}")
			paragraph = paragraph[ChapterCounterLength:]
			paragraph = paragraph.strip()
			self.set_name(paragraph)

	def __UnwrapTags(self, paragraph: BeautifulSoup) -> BeautifulSoup:
		"""
		Раскрывает вложенные одноимённые теги.

		:param paragraph: Обрабатываемый абзац.
		:type paragraph: BeautifulSoup
		:return: Обработанный абзац.
		:rtype: BeautifulSoup
		"""

		AllowedTags = list(self.__AllowedTags.keys())
		AllowedTags.remove("blockquote")
		AllowedTags = tuple(AllowedTags)

		for Tag in self.__AllowedTags.keys():
			for Parent in paragraph.find_all(Tag):
				for Child in Parent.find_all(Tag): Child.unwrap()

		return paragraph

	def __ValidateHTML(self, paragraph: BeautifulSoup, exceptions: bool = True) -> BeautifulSoup:
		"""
		Проверяет соответствие абзаца допустимым спецификациям HTML.

		:param paragraph: Проверяемый абзац.
		:type paragraph: BeautifulSoup
		:param exceptions: Указывает, нужно ли выбрасывать соответствующие исключения. По умочанию `True`.
		:type exceptions: bool, optional
		:return: Обработанный абзац.
		:rtype: BeautifulSoup
		"""
		
		for Tag in paragraph.find_all():

			if Tag.name not in self.__AllowedTags.keys():
				self._SystemObjects.logger.error(f"Unresolved tag \"{Tag.name}\".")
				if exceptions: raise UnresolvedTag(Tag)

			else:
				Attributes = Tag.attrs.copy()

				for Attribute in Tag.attrs:
					if Attribute not in self.__AllowedTags[Tag.name]:
						del Attributes[Attribute]
						self._SystemObjects.logger.warning(f"Unresolved attribute \"{Attribute}\" in \"{Tag.name}\" tag. Removed.")

				Tag.attrs = Attributes

		return paragraph

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", title: "Ranobe"):
		"""
		Глава ранобэ.
			system_objects – коллекция системных объектов;\n
			title – данные тайтла.
		"""

		self._SystemObjects = system_objects
		self.__Title = title

		self._Chapter = {
			"id": None,
			"slug": None,
			"volume": None,
			"number": None,
			"name": None,
			"type": None,
			"is_paid": None,
			"workers": [],
			"paragraphs": []	
		}
		self._ParserSettings = system_objects.manager.current_parser_settings

		self.__AllowedTags = {
			"p": ("align",),
			"b": (),
			"i": (),
			"s": (),
			"u": (),
			"sup": (),
			"sub": (),
			"img": ("src",),
			"blockquote": ("data-name",)
		}

		self._SetParagraphsMethod = self.set_paragraphs
		self._SetSlidesMethod = self._Pass

	def add_paragraph(self, paragraph: str):
		"""
		Добавляет абзац в главу. Если текст не обёрнут в тег `<p>`, это будет выполнено автоматически.

		:param paragraph: Текст абзаца с поддерживаемой HTML разметкой.
		:type paragraph: str
		"""

		paragraph = paragraph.strip()
		if not paragraph.startswith("<p"): paragraph = f"<p>{paragraph}</p>"
		
		if self._ParserSettings.common.pretty:
			Tag = BeautifulSoup(paragraph, "html.parser").find("p")
			if not Tag.text and not Tag.find("img"): return
			
			#---> Форматирование тегов и атрибутов.
			#==========================================================================================#
			Align = ""
			InnerHTML = Tag.decode_contents().strip()
			if Tag.has_attr("align"): Align = " align=\"" + Tag["align"] + "\""
			InnerHTML = HTML(InnerHTML)
			InnerHTML.remove_tags(["br", "ol", "ul"])
			InnerHTML.replace_tag("em", "i")
			InnerHTML.replace_tag("strong", "b")
			InnerHTML.replace_tag("strike", "s")
			InnerHTML.replace_tag("del", "s")
			InnerHTML.replace_tag("li", "p")
			InnerHTML.unescape()
			Tag = BeautifulSoup(f"<p{Align}>{InnerHTML.text}</p>", "html.parser")

			Tag = self.__UnwrapTags(Tag)
			self.__ValidateHTML(Tag)

			#---> Преобразование символьных последовательностей.
			#==========================================================================================#
			paragraph = str(Tag)
			paragraph = paragraph.replace("\u00A0", " ")
			paragraph = RemoveRecurringSubstrings(paragraph, " ")
			paragraph = paragraph.replace(" \n", "\n")
			paragraph = paragraph.replace("\n ", "\n")

			#---> Определение валидности абзаца.
			#==========================================================================================#
			IsValid = True

			if not Tag.text.strip(" \t\n.") and not Tag.find("img"):
				IsValid = False

			elif len(self._Chapter["paragraphs"]) <= 3:
				Paragraph = Tag.text.rstrip(".!?…").lower()
				ChapterName = self.name.rstrip(".!?…").lower() if self.name else None
				LocalizedName = self.__Title.localized_name.rstrip(".!?…").lower() if self.__Title.localized_name else None
				LocalizedChapterWord = self.__GetLocalizedChapterWord()

				if ChapterName and Paragraph == ChapterName: IsValid = False
				elif LocalizedName and Paragraph == LocalizedName: IsValid = False
				elif LocalizedChapterWord and f"{LocalizedChapterWord} {self.number}" in Paragraph:
					IsValid = False
					self.__TryGetName(Tag.text)

			if not IsValid: return

		paragraph = self.__DownloadImages(paragraph)
		self._Chapter["paragraphs"].append(self._ParserSettings.filters.text.clear(paragraph))

	def clear_paragraphs(self):
		"""Удаляет содержимое главы."""

		self._Chapter["paragraphs"] = list()

	def set_name(self, name: str | None):
		"""
		Задаёт название главы.
			name – название главы.
		"""

		if not name:
			self._Chapter["name"] = None
			return

		if name.endswith("..."):
			name = name.rstrip(".")
			name += "…"

		else: 
			name = name.rstrip(".–")

		name = name.replace("\u00A0", " ")
		name = name.lstrip(":")
		name = name.strip()
		self._Chapter["name"] = name

	def set_paragraphs(self, paragraphs: list[str]):
		"""
		Задаёт список абзацев.
			slides – список абзацев.
		"""

		for Paragraph in paragraphs: self.add_paragraph(Paragraph)

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

class Ranobe(BaseTitle):
	"""Ранобэ."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def original_language(self) -> str | None:
		"""Оригинальный язык контента по стандарту ISO 639-3."""

		return self._Title["original_language"]

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

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
		"""Объединяет данные описательного файла и текущей структуры данных."""

		Path = f"{self._ParserSettings.common.titles_directory}/{self._UsedFilename}.json"
		
		if os.path.exists(Path) and not self._SystemObjects.FORCE_MODE:
			LocalRanobe = ReadJSON(Path)
			LocalContent = dict()
			MergedChaptersCount = 0

			if LocalRanobe["format"] != "melon-ranobe":
				self._SystemObjects.logger.unsupported_format(self)
				return
			
			for BranchID in LocalRanobe["content"]:
				for CurrentChapter in LocalRanobe["content"][BranchID]: LocalContent[CurrentChapter["id"]] = CurrentChapter["paragraphs"]
			
			for BranchID in self._Title["content"]:
		
				for ChapterIndex in range(len(self._Title["content"][BranchID])):
				
					if self._Title["content"][BranchID][ChapterIndex]["id"] in LocalContent.keys():
						ChapterID = self._Title["content"][BranchID][ChapterIndex]["id"]

						if LocalContent[ChapterID]:
							self._Title["content"][BranchID][ChapterIndex]["paragraphs"] = LocalContent[ChapterID]
							MergedChaptersCount += 1

			self._SystemObjects.logger.merging_end(self, MergedChaptersCount)

		self._Branches = list()

		for CurrentBranchID in self._Title["content"].keys():
			BranchID = int(CurrentBranchID)
			NewBranch = Branch(BranchID)

			for ChapterData in self._Title["content"][CurrentBranchID]:
				NewChapter = Chapter(self._SystemObjects, self)
				NewChapter.set_dict(ChapterData)
				NewBranch.add_chapter(NewChapter)

			self.add_branch(NewBranch)

	def repair(self, chapter_id: int):
		"""
		Восстанавливает содержимое главы, заново получая его из источника.
			chapter_id – уникальный идентификатор целевой главы.
		"""

		SearchResult = self._FindChapterByID(chapter_id)
		if not SearchResult: raise ChapterNotFound(chapter_id)

		BranchData: Branch = SearchResult[0]
		ChapterData: Chapter = SearchResult[1]
		ChapterData.clear_paragraphs()
		self._Parser.amend(BranchData, ChapterData)

		if ChapterData.paragraphs: self._SystemObjects.logger.chapter_repaired(self, ChapterData)

	#==========================================================================================#
	# >>>>> МЕТОДЫ УСТАНОВКИ СВОЙСТВ <<<<< #
	#==========================================================================================#

	def set_original_language(self, original_language: str | None):
		"""
		Задаёт оригинальный язык контента по стандарту ISO 639-3.
			original_language – код языка.
		"""

		if type(original_language) == str and len(original_language) != 3: raise TypeError(original_language)
		self._Title["original_language"] = original_language.lower() if original_language else None