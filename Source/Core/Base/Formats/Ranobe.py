from Source.Core.Base.Formats.Components.WorldsDictionary import CheckLanguageCode
from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseBranch, BaseTitle
from Source.Core import Exceptions

from dublib.Methods.Data import RemoveRecurringSubstrings, Zerotify
from dublib.Methods.Filesystem import ReadJSON
from dublib.Engine.Bus import ExecutionStatus
from dublib.Polyglot import HTML

from typing import Any, Iterable, Literal, TYPE_CHECKING
from pathlib import Path
from os import PathLike
from time import sleep
import base64
import enum
import os
import re

from bs4 import BeautifulSoup

from urllib.parse import urlparse, unquote

if TYPE_CHECKING:
	from Source.Core.Base.Formats.Components import WordsDictionary
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

class ChapterHeaderParser:
	"""Парсер заголовка главы."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def volume(self) -> str | None:
		"""Номер тома."""

		return self._Volume
	
	@property
	def number(self) -> str | None:
		"""Номер главы."""

		return self._Number
	
	@property
	def type(self) -> ChaptersTypes | None:
		"""Тип главы."""

		return self._Type
	
	@property
	def name(self) -> str | None:
		"""Название главы."""

		return Zerotify(self._Title)

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _GetType(self):
		"""Получает тип главы из заголовка."""

		Determinations = {
			ChaptersTypes.prologue: self._WordsDictionary.prologue,
			ChaptersTypes.epilogue: self._WordsDictionary.epilogue,
			ChaptersTypes.art: self._WordsDictionary.art,
			ChaptersTypes.afterword: self._WordsDictionary.afterword,
			ChaptersTypes.glossary: self._WordsDictionary.glossary,
			ChaptersTypes.extra: self._WordsDictionary.extra,
		}

		LowerTitle = self._Title.lower()

		for ChapterType, Word in Determinations.items():
			if LowerTitle.startswith(Word):
				self._Type = ChapterType
				break

	def _ExtractNumber(self, only_for_chapter: bool = False):
		"""
		Извлекает номер главы из заголовка.

		:param onky_for_chapter: Указывает, следует ли использовать все ключевые слова для извлечения номера или только ключеввое слово главы.
		:type onky_for_chapter: bool
		"""

		Keywords = (self._WordsDictionary.chapter,)

		if not only_for_chapter:
			Keywords = list(self._WordsDictionary.keywords)
			if self._WordsDictionary.volume: Keywords.remove(self._WordsDictionary.volume)

		for Keyword in Keywords:
			KeywordMatch = re.search(f"\\b{Keyword}\\s*([\\d\\.]+)", self._Title, re.IGNORECASE)

			if KeywordMatch:
				self._Number = KeywordMatch.group(1).rstrip(".")
				break

	def _ExtractVolume(self):
		"""Извлекает номер тома из заголовка."""

		VolumeMatch = re.search(f"\\b{self._WordsDictionary.volume}\\s*(\\d+)[^\\d]?", self._Title, re.IGNORECASE)
		if VolumeMatch: self._Volume = VolumeMatch.group(1)

	def _LeftCutTitle(self, value: str):
		"""
		Обрезает строку с левого конца до переданного значения.

		:param value: Значение, по которому производится разрез.
		:type value: str
		"""

		TitleParts = self._Title.split(value)
		if len(TitleParts) < 2: return
		self._Title = value.join(TitleParts[1:])

	def _LstripTitle(self):
		"""Удаляет из начала строки небуквенные символы за исключением `…`."""

		ChapterStart = str()

		for Character in self._Title:
			if not Character.isalpha(): ChapterStart += Character
			else: break

		self._Title = self._Title[len(ChapterStart):]
		if ChapterStart.count(".") >= 3 or "…" in ChapterStart: self._Title = f"…{self._Title}"

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЙ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, title: str, words_dictionary: WordsDictionary):
		"""
		Парсер заголовка главы.

		:param title: Заголовок главы.
		:type title: str
		:param words_dictionary: Словарь ключевых слов.
		:type words_dictionary: WordsDictionary
		"""

		self._Title = title
		self._WordsDictionary = words_dictionary

		self._Volume = None
		self._Number = None
		self._Type = None
	
	def __repr__(self) -> str:
		"""Реинтерпретирует экземпляр в строковое представление."""
		
		return f"ChapterData(volume={self.volume}, number={self.number}, type={self.type}, name={self.__Title})"
	
	def parse(self) -> "ChapterHeaderParser":
		"""
		Парсит заголовок главы.

		:return: Парсер заголовка главы.
		:rtype: ChapterTitleParser
		"""

		self._ExtractVolume()
		if self._Volume: self._LeftCutTitle(self._Volume)
		self._LstripTitle()
		self._GetType()
		self._ExtractNumber()
		if self._Number: self._LeftCutTitle(self._Number)
		self._LstripTitle()

		return self

class IllustrationData:
	"""Данные иллюстрации."""

	@property
	def directory(self) -> PathLike:
		"""Путь к каталогу хранения иллюстрации."""

		return self.__Directory

	@property
	def path(self) -> PathLike:
		"""Путь к файлу иллюстрации."""

		return self.__PathObject.as_posix()
	
	@property
	def is_exists(self) -> bool:
		"""Состояние: найдена ли иллюстрация в собственном каталоге."""

		return self.__IsExists

	@property
	def mounted_path(self) -> PathLike:
		"""Путь к файлу иллюстрации внутри каталога выхода."""

		return self.__MountedPath

	def __init__(self, title: "Ranobe", chapter: "Chapter", filename: str):
		"""
		Данные иллюстрации.

		:param title: Данные тайтла.
		:type title: Ranobe
		:param chapter: Данные главы.
		:type chapter: Chapter
		:param filename: Имя файла.
		:type filename: str
		"""

		self.__MountedPath = f"{title.used_filename}/illustrations/{chapter.id}/{filename}"
		self.__Directory = f"{title.parser.settings.common.images_directory}/{title.used_filename}/illustrations/{chapter.id}"
		self.__PathObject = Path(f"{self.__Directory}/{filename}")
		self.__IsExists = os.path.exists(self.path)

		os.makedirs(self.__Directory, exist_ok = True)

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

	def __DecodeImageFromBase64(self, image: BeautifulSoup):
		"""
		Декодирует изображение из **Base64**.

		:param image: Тег изображения.
		:type image: BeautifulSoup
		"""

		Data = image["src"][5:]
		Mime, Data = Data.split(";")
		Filetype, Data = Mime.split("/")[-1], Data[7:].strip()
		Filename = Data.replace("/", "").replace("+", "")[:16] + f".{Filetype}"
		Illustration = IllustrationData(self._Title, self, Filename)

		print(f"Decoding Base64 image: \"{Filename}\"… ", end = "")
		Message = "Done."
		
		if not Illustration.is_exists or self._SystemObjects.FORCE_MODE:
			ImageBytes = base64.b64decode(Data)
			image.attrs = {"src": Illustration.mounted_path}
			with open(Illustration.path, "wb") as FileWriter: FileWriter.write(ImageBytes)
			if Illustration.is_exists: Message = "Overwritten."

		else: Message = "Already exists."
		
		print(Message)
		
	def __DownloadImages(self, paragraph: str) -> str:
		"""
		Скачивает иллюстрации из абзаца.

		:param paragraph: Абзац текста.
		:type paragraph: str
		:return: Абзац с заменённым путями изображений в тегах `img`.
		:rtype: str
		"""

		Parser = self._Title.parser
		Soup = BeautifulSoup(paragraph, "html.parser")
		Images = Soup.find_all("img")
		
		for Image in Images:
			Link = Image.get("src")

			if not Link: 
				self._SystemObjects.logger.warning("Image decomposed because has not source.")
				Image.decompose()
				continue

			if Link.startswith("data:"):
				self.__DecodeImageFromBase64(Image)
				continue

			Filename = os.path.basename(unquote(urlparse(Link).path))
			Illustration = IllustrationData(self._Title, self, Filename)
			print(f"Downloading image: \"{Filename}\"… ", end = "")
			
			if Illustration.is_exists and not self._SystemObjects.FORCE_MODE:
				Image.attrs = {"src": Illustration.mounted_path}
				print("Already exists.")
				continue
			
			Status = Parser.image(Link)

			if Status:
				sleep(Parser.settings.common.delay)
				Image.attrs = {"src": Illustration.mounted_path}
				Parser.images_downloader.move_from_temp(Illustration.directory, Status.value)

			if Illustration.is_exists and Status:
				Status = ExecutionStatus()
				Status.push_message("Overwritten.")

			Status.print_messages()

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
				Style = Style.strip()
				if not Style: continue
				Name, Value = Style.split(":")
				Name, Value = Name.strip(), Value.strip()
				tag.attrs = {"align": Value}
				if Name == "text-align" and Value in Aligns: return Value

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

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param title: Данные тайтла.
		:type title: Ranobe
		"""

		self._SystemObjects = system_objects
		self._Title = title

		self._ParserSettings = system_objects.manager.current_parser_settings
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

	def __setitem__(self, key: str, value: Any):
		"""
		Устанавливает значение напрямую в структуру данных по ключу.

		:param key: Ключ.
		:type key: str
		:param value: Значение.
		:type value: Any
		"""

		self._Chapter[key] = value

	def add_paragraph(self, paragraph: str):
		"""
		Добавляет абзац в главу. Если текст не обёрнут в тег `<p>`, это будет выполнено автоматически.

		Указанные в тегах `<img>` изображения будут автоматически скачаны. Также поддерживается декодирование **Base64**.

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
			if not Tag.text.strip(" \t\n.") and not Tag.find("img"): return

			if len(self.paragraphs) <= 3:
				Paragraph = Tag.text.rstrip(".!?…").lower()
				ChapterLowerName, LocalizedLowerName = (None, None)

				if self.name: ChapterLowerName = self.name.rstrip(".!?…").lower()
				if self._Title.localized_name: LocalizedLowerName = self._Title.localized_name.rstrip(".!?…").lower()

				if ChapterLowerName and Paragraph == ChapterLowerName: return
				if LocalizedLowerName and Paragraph == LocalizedLowerName: return

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
			
		if name:
			if name.endswith("..."): name = name.rstrip(".") + "…"
			else: name = name.rstrip(".–")
			if name.startswith("..."): name = "…" + name.lstrip(".")

			name = name.replace("\u00A0", " ")
			name = name.strip(":.")

		super().set_name(name)

	def set_paragraphs(self, paragraphs: Iterable[str]):
		"""
		Задаёт набор абзацев.

		:param paragraphs: Набор абзацев.
		:type paragraphs: Iterable[str]
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
	# >>>>> СВОЙСТВА ТАЙТЛА <<<<< #
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
					Container["paragraphs"] = Paragraphs
					MergedChaptersCount += 1
	
			self._SystemObjects.logger.merging_end(self, MergedChaptersCount)

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