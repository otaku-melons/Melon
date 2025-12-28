from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseBranch, BaseTitle
from Source.Core import Exceptions

from dublib.Methods.Data import RemoveRecurringSubstrings
from dublib.Methods.Filesystem import ReadJSON
from dublib.Methods.Data import Zerotify
from dublib.Polyglot import HTML

from typing import Literal, TYPE_CHECKING
from dataclasses import dataclass
from pathlib import Path
from time import sleep
import enum
import os
import re

from bs4 import BeautifulSoup

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

@dataclass
class ChapterData:
	"""Контейнер основных данных главы."""

	volume: str | None
	number: str | None
	name: str | None

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
				
				if os.path.exists(f"Output/{ImageTagSource}"):
					Image.attrs = {"src": ImageTagSource}
					Message = "Already exists."

				else:
					Status = Parser.image(Link)
					if Status.has_errors: continue
					if not Status["exists"]: sleep(Parser.settings.common.delay)
					Filename = Status.value

					if Filename: 
						Image.attrs = {"src": ImageTagSource}
						os.makedirs(Directory, exist_ok = True)
						Result = Parser.images_downloader.move_from_temp(Directory, Filename)

						if Result.value and Result["exists"]:
							if self._SystemObjects.FORCE_MODE: Message = "Overwritten."
							else: Message = "Already exists."

				print(Message)

			else: 
				self._SystemObjects.logger.warning("Image decomposed because has not source.")
				Image.decompose()

		return str(Soup)

	def __GetAlignForParagraph(self, tag: BeautifulSoup) -> Literal["left", "right", "centet"] | None:
		"""
		Получает тип выравнивания для тега `p`. Автоматически применяет изменения к тегу.

		:param tag: Тег `p`.
		:type tag: BeautifulSoup
		:return: Тип выравнивания или `None`, если таковой не поддерживается.
		:rtype: Literal["left", "right", "centet"] | None
		"""

		if tag.name != "p": return
		Aligns = ("left", "right", "center")

		if "align" in tag.attrs:
			Align = tag.attrs["align"].strip()
			tag.attrs = {"align": Align}
			if Align in Aligns: return Align

		if "style" in tag.attrs:
			Styles = tag.attrs["style"].split(";")

			for Style in Styles:
				Name, Value = Style.split(":")
				Name, Value = Name.strip(), Value.strip()
				tag.attrs = {"align": Value}
				if Name == "text-align" and Value in Aligns: return Value

	def __GetLocalizedChapterWord(self) -> str | None:
		"""Возвращает слово в нижнем регистре, обозначающее главу."""

		Words = {
			"rus": "глава",
			"eng": "chapter"
		}

		return Words.get(self.__Title.content_language)
			
	def __TryParseChapterMainData(self, name: str) -> ChapterData | None:
		"""
		Пытается получить номер тома, главы и название по отдельности из названия главы.

		:param name: Название главы.
		:type name: str
		:return: Контейнер основных данных главы или `None` в случае неудачи.
		:rtype: ChapterData | None
		"""

		Volume, Number, Name = None, None, None
		VolumeWord = "том"
		ChapterWord = "глава"	

		VolumeMatch = re.search(f"\\b{VolumeWord}\\s*(\\d+)[^\\d]?", name, re.IGNORECASE)
		if VolumeMatch: Volume = VolumeMatch.group(1)

		ChapterMatch = re.search(f"\\b{ChapterWord}\\s*([\\d\\.]+)", name, re.IGNORECASE)
		if ChapterMatch: Number = ChapterMatch.group(1)

		if not Number:
			StartNumber = re.match(r"^(\d+)", name)
			if StartNumber and not Volume: Number = StartNumber.group(1)

		if Volume:
			NameParts = name.split(Volume)[1:]
			name = Volume.join(NameParts)

		if Number:
			NameParts = name.split(Number)[1:]
			name = Number.join(NameParts)

		Name = Zerotify(name)

		return ChapterData(Volume, Number, Name)

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
				if exceptions: raise Exceptions.UnresolvedTag(Tag)

			else:
				Attributes = Tag.attrs.copy()

				for Attribute in Tag.attrs:
					if Attribute not in self.__AllowedTags[Tag.name] and not Attribute.startswith("data-"):
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
			"img": ("src", "data-width", "data-height"),
			"blockquote": ("data-name", "data-icon", "data-color")
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
			InnerHTML = Tag.decode_contents().strip()
			InnerHTML = HTML(InnerHTML)
			InnerHTML.remove_tags(("br", "ol", "ul"))
			InnerHTML.replace_tag("em", "i")
			InnerHTML.replace_tag("strong", "b")
			InnerHTML.replace_tag("strike", "s")
			InnerHTML.replace_tag("del", "s")
			InnerHTML.replace_tag("li", "p")

			Align = self.__GetAlignForParagraph(Tag)
			if Align: Align = f" align=\"{Align}\""
			else: Align = ""

			Tag = BeautifulSoup(f"<p{Align}>{InnerHTML.text}</p>", "html.parser")
			Blockquote = Tag.find("blockquote")

			if Blockquote:
				for P in Blockquote.find_all("p"): self.__GetAlignForParagraph(P)

			else: Tag = self.__UnwrapTags(Tag)

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
				elif all((LocalizedChapterWord, self.number)) and LocalizedChapterWord in Paragraph.lower() and self.number in Paragraph:
					IsValid = False
					MainData = self.__TryParseChapterMainData(paragraph)
					if not self.volume: self.set_volume(MainData.volume)
					if not self.number: self.set_number(MainData.number)
					if not self.name: self.set_name(MainData.name)

			if not IsValid: return

		paragraph = self.__DownloadImages(paragraph)
		paragraph = HTML(paragraph).unescape()
		self._Chapter["paragraphs"].append(self._ParserSettings.filters.text.clear(paragraph))

	def clear_paragraphs(self):
		"""Удаляет содержимое главы."""

		self._Chapter["paragraphs"] = list()

	def set_name(self, name: str | None):
		"""
		Задаёт название главы. В случае включения опции _pretty_ для парсера, производит очистку и пытается извлечь номер главы.

		:param name: Название главы.
		:type name: str | None
		"""

		if name and self._ParserSettings.common.pretty:
			MainData = self.__TryParseChapterMainData(name)
			if not self.volume: self.set_volume(MainData.volume)
			if not self.number: self.set_number(MainData.number)
			if MainData.name: name = MainData.name
			
			if name.endswith("..."):
				name = name.rstrip(".")
				name += "…"

			else: name = name.rstrip(".–")

			if name.startswith("..."):
				name = name.lstrip(".")
				name = "…" + name

			name = name.replace("\u00A0", " ")
			name = name.lstrip(":.")
			
		if name: name = name.strip()
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
				self._SystemObjects.logger.unsupported_format(self)
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
					Container.set_paragraphs(Paragraphs)
					MergedChaptersCount += 1
	
			self._SystemObjects.logger.merging_end(self, MergedChaptersCount)

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