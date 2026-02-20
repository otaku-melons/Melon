from Source.Core import Exceptions

from dublib.Methods.Data import RemoveRecurringSubstrings
from dublib.Polyglot import HTML

from typing import Literal, TYPE_CHECKING
from pathlib import Path
import base64
import uuid
import os

from bs4 import BeautifulSoup, Tag
import validators

if TYPE_CHECKING:
	from . import Chapter

	from Source.Core.Base.Parsers.Components.ImagesDownloader import ImageResolution
	from Source.Core.Base.Parsers.RanobeParser import RanobeParser

	from Source.Core.SystemObjects import SystemObjects

class Footnote:
	"""
	Заметка.

	Для использования поместите уникальный идентификатор заметки в текст абзаца внутри фигурных скобок `{e2c3e8a4-...}` и прикрепите заметку к абзацу. Комбинация UUID и скобочек должна быть уникальна в разрезе абзаца. Компоновка HTML будет выполнена автоматически и полученный якорь заменит идентификатор.
	"""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def placeholder(self) -> str:
		"""Отображаемый текст заметки."""

		return self.__Placeholder

	@property
	def uuid(self) -> str:
		"""Уникальный идентификатор заметки."""

		return self.__UUID
	
	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Заметка.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__SystemObjects = system_objects

		self.__Logger = self.__SystemObjects.logger
		
		self.__UUID = str(uuid.uuid4())
		self.__Elements: list[Paragraph | Image] = list()
		self.__Placeholder = "*"
		self.__ImagesCount = 0

	def add_element(self, element: "Paragraph | Image"):
		"""
		Добавляет элемент заметки.

		Добавляемый абзац не должен содержать заметок, а изображение следует передавать только одно.

		:param element: Элемент заметки.
		:type element: Paragraph | Image
		:raise RecursionError: Выбрасывается при передаче абзаца с заметкой.
		"""

		if type(element) == Paragraph:
			if element.footnotes: raise RecursionError("Paragraph can't contain footnotes.")
			self.__Elements.append(element)
			return
		
		if type(element) == Image:
			self.__Elements.append(element)
			self.__ImagesCount += 1
			if self.__ImagesCount > 1: self.__Logger.warning("Footnote should contain only one image.")

	def set_placeholder(self, placeholder: str):
		"""
		Задаёт отображаемый текст заметки. Обычно используются такие индикаторы, как `[1]` или `*`.

		:param placeholder: Отображаемый текст заметки.
		:type placeholder: str
		"""

		self.__Placeholder = placeholder

	def refresh_uuid(self) -> str:
		"""
		Обновляет уникальный идентификатор заметки. Вычисляется при помощи функции `uuid4()`.

		:return: Уникальный идентификатор заметки.
		:rtype: str
		"""

		self.__UUID = str(uuid.uuid4())

		return self.__UUID

	def replace_in_text(self, text: str, alias: str, max_iterations: int = 10) -> str:
		"""
		Заменяет в передаваемом тексте подстроку на идентификатор заметки. Гарантирует уникальность последнего в разряде абзаца.

		:param text: Обрабатываемый текст.
		:type text: str
		:param alias: Заменяемая на идентификатор подстрока. Должна быть уникальна в абзаце.
		:type alias: str
		:param max_iterations: Максимальное количество итераций подбора.
		:type max_iterations: int
		:return: Обработанный текст или `None` в случае неудачи.
		:rtype: str | None
		:raise ValueError: Выбрасывается, если в строке несколько вхождений заменяемой подстроки.
		"""

		if text.count(alias) > 1: raise ValueError("Alias must be unique in text.")
		FootnoteID = "{" + self.__UUID + "}"
		IsReplaced = False
		Iteration = 0

		while not IsReplaced:
			Iteration += 1
			if Iteration > max_iterations: break

			if FootnoteID not in text:
				text = text.replace(alias, FootnoteID)
				IsReplaced = True

			else:
				self.refresh_uuid()
				FootnoteID = "{" + self.__UUID + "}"

		return text

	def to_html(self) -> str:
		"""
		Возвращает HTML представление заметки.

		:return: HTML представление заметки.
		:rtype: str
		:raise ValueError: Выбрасывается, если заметка пустая.
		"""

		if not self.__Elements: raise ValueError("Footnote must contain elements.")

		return "".join(Element.to_html() for Element in self.__Elements)

class Header:
	"""Заголовок."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def footnotes(self) -> tuple[Footnote]:
		"""Набор заметок."""

		return tuple(self._Footnotes)
	
	#==========================================================================================#
	# >>>>> ЗАЩИЩЁННЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _GetFootnotedText(self, offset: int | None) -> str:
		"""
		Возвращает текст с якорями заметок.

		:param offset: Сдвиг для индексации заметок.
		:type offset: int | None
		:return: Текст с якорями заметок.
		:rtype: str
		"""

		if not self._Text: raise Exceptions.FootnoteCompositionError("Text must be setted before footnotes compositing.")
		Text = self._Text

		FootnoteIndex = 0
		if offset: FootnoteIndex += offset

		for CurrentNote in self._Footnotes:
			FootnoteID = "{" + CurrentNote.uuid + "}"
			if FootnoteID not in self._Text: raise Exceptions.FootnoteCompositionError("Footnote UUID not found in text.")
			Text = Text.replace(FootnoteID, f"<a href=\"#{FootnoteIndex}\">{CurrentNote.placeholder}</a>")
			self._SystemObjects.logger.info(f"Footnote with index {FootnoteIndex} added.")
			FootnoteIndex += 1

		return Text
	
	def _PrettyText(self, text: str) -> str:
		"""
		Улучшает качество текста благодаря исправлению форматирования.

		:param text: Обрабатываемый текст.
		:type text: str
		:return: Обработанный текст.
		:rtype: str
		"""

		#---> Удаление дублирующихся пробелов.
		#==========================================================================================#
		text = text.replace("\u00A0", " ")
		text = RemoveRecurringSubstrings(text, " ")

		#---> Удаление пробельных символов в начале и конце строк.
		#==========================================================================================#
		TextFragments = list()

		for Fragment in text.split("\n"):
			Fragment = Fragment.strip()
			if not Fragment: continue
			TextFragments.append(Fragment)

		text = "\n".join(TextFragments)

		return text

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Заголовок.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self._SystemObjects = system_objects

		self._Text = None
		self._Align = None
		self._Footnotes: list[Footnote] = list()
		self._WrapperTag = "h3"

	def add_footnote(self, footnote: Footnote):
		"""
		Добавляет заметку и выполняет композицию HTML абзаца.

		:param footnote: Заметка.
		:type footnote: Footnote
		"""

		self._Footnotes.append(footnote)

	def parse_align(self, data: str | Tag) -> Literal["right", "centet"] | None:
		"""
		Пытается получить тип выравнивания из переданного тега HTML на основании атрибутов _align_ и _style_. Если передать строку, будет произведён автоматический парсинг.

		При успешном получении типа отличного от `None` изменения автоматически применяются к объекту.

		:param data: HTML для парсинга.
		:type data: str | Tag
		:return: Тип выравнивания или `None`, если таковой не обнаружен или не поддерживается.
		:rtype: Literal["right", "centet"] | None
		"""

		Tag = BeautifulSoup(data, "html.parse").find("p") if type(data) == str else data

		if Tag.name != "p": return
		Aligns = ("center", "right")
		Align = None

		if "align" in Tag.attrs:
			AlignData = Tag.attrs["align"].strip()
			Tag.attrs = {"align": AlignData}
			if AlignData in Aligns: Align = AlignData

		elif "style" in Tag.attrs:
			Styles = Tag.attrs["style"].split(";")

			for Style in Styles:
				Style = Style.strip()
				if not Style: continue
				Name, Value = Style.split(":")
				Name, Value = Name.strip(), Value.strip()
				Tag.attrs = {"align": Value}
				if Name == "text-align" and Value in Aligns: Align = Value

		if Align: self.set_align(Align)

		return Align

	def set_align(self, align: Literal["center", "right", None]):
		"""
		Задаёт выравнивание абзаца.

		:param align: Выравнивание абзаца.
		:type align: Literal["center", "right", None]
		:raises ValueError: Выбрасывается при установке неподдерживаемого выравнивания.
		"""

		if align not in ("center", "right", None): raise ValueError("Align isn't supported.")
		self._Align = align

	def set_text(self, text: str):
		"""
		Задаёт текст заголовка.

		:param text: Текст заголовка.
		:type text: str
		:raise ValueError: Выбрасывается при передаче неверно отформатированного текста.
		:raise UnresolvedTag: Выбрасывается при наличии неразрешённого тега в тексте.
		"""

		text = text.strip()
		if not text: raise ValueError("Text can't be empty.")
		text = HTML(text).plain_text
		self._Text = text

	def to_html(self, footnotes_offset: int | None = None) -> str | None:
		"""
		Возращает HTML представление абзаца.

		:param footnotes_offset: Сдвиг для индексации заметок. При отсутствии нумерация с нуля.
		:type footnotes_offset: int | None
		:return: HTML представление абзаца.
		:rtype: str | None
		:raise FootnoteCompositionError: Выбрасывается при ошибке композиции заметки.
		"""

		if not self._Text: return None
		Text = self._GetFootnotedText(footnotes_offset)
		Align = f" align=\"{Align}\"" if self._Align else ""

		return f"<{self._WrapperTag}{Align}>{Text}</{self._WrapperTag}>"

class Image:
	"""Иллюстрация."""

	def __init__(self, system_objects: "SystemObjects", parser: "RanobeParser", chapter: "Chapter"):
		"""
		Иллюстрация.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param parser: Парсер ранобэ.
		:type parser: RanobeParser
		:param chapter: Данные главы.
		:type chapter: Chapter
		"""

		self.__SystemObjects = system_objects
		self.__Parser = parser
		self.__ImagesDownloader = self.__Parser.images_downloader
		self.__Title = self.__Parser.title
		self.__Chapter = chapter

		self.__Logger = self.__SystemObjects.logger

		self.__Directory = f"{self.__Title.parser.settings.common.images_directory}/{self.__Title.used_filename}/illustrations/{chapter.id}"
		self.__RealPath: str = None
		self.__MountedPath: str = None
		self.__Filename: str = None
		self.__IsExists: bool = None
		self.__Sizes: "ImageResolution | None" = None

		os.makedirs(self.__Directory, exist_ok = True)

	def decode_from_base64(self, data: str):
		"""
		Декодирует изображение из **Base64**.

		:param data: Данные в кодировке **Base64**.
		:type data: str
		:raises ValueError: Выбрасывается при некорректной кодировке **Base64**.
		"""

		if data.startswith("base:"): data = data[5:]
		if not validators.base64(data): raise ValueError("Invalid Base64 encoding.")
		print(f"Decoding image \"{self.__Filename}\" from Base64… ", end = "")

		Mime, Data = data.split(";")
		Filetype, Data = Mime.split("/")[-1], Data[7:].strip()
		Filename = Data.replace("/", "").replace("+", "")[:16] + f".{Filetype}"
		self.rename(Filename)

		if self.__IsExists:
			print("Already exists.")
			self.__Logger.info(f"Illustration \"{self.__Filename}\" already exists.")
			return

		ImageBytes = base64.b64decode(Data)
		self.__Sizes = self.__ImagesDownloader.get_image_resolution(ImageBytes)
		with open(self.__RealPath, "wb") as FileWriter: FileWriter.write(ImageBytes)
		print("Done.")
		self.__Logger.info(f"Image \"{self.__Filename}\" decoded from Base64.")

	def parse_image(self, data: str | Tag):
		"""
		Парсит изображение из тега HTML.

		:param data: Строковое представление HTML или тег.
		:type data: str | Tag
		"""

		data = BeautifulSoup(data, "html.parser").find("img") if type(data) == str else data
		Source = data.get("src")

		if not Source: 
			self.__Logger.warning("Image hasn't source. Skipped.")
			return

		if Source.startswith("data:"): self.decode_from_base64(Source)
		else: self.set_link(Source)	

	def rename(self, filename: str):
		"""
		Задаёт имя файла для иллюстрации.

		:param filename: Имя файла с расширением.
		:type filename: str
		:raise TypeError: Выбрасывается при передаче неверного типа данных.
		"""

		if type(filename) != str: raise TypeError("Filename must be a string.")

		self.__Filename = filename
		self.__RealPath = f"{self.__Directory}/{filename}"
		self.__IsExists = os.path.exists(self.__RealPath)
		self.__MountedPath = f"{self.__Title.used_filename}/illustrations/{self.__Chapter.id}/{filename}"

	def set_link(self, link: str):
		"""
		Задаёт ссылку на иллюстрацию.

		:param link: Ссылка на иллюстрацию.
		:type link: str
		:raises ValueError: Выбрасывается при некорректном URL.
		"""

		if not validators.url(link): raise ValueError("Invalid URL.")
		LinkPath = Path(link)
		self.rename(LinkPath.name)
		print(f"Downloading image: \"{self.__Filename}\"… ", end = "")
		Result = self.__ImagesDownloader.image(link, self.__Directory)
		self.__Sizes = Result["resolution"]
		Result.print_messages()

	def to_html(self) -> str:
		"""
		Возращает HTML представление иллюстрации.

		:return: HTML представление иллюстрации.
		:rtype: str
		"""

		Sizes = ""
		if self.__Sizes: Sizes = f" data-width=\"{self.__Sizes.width}\" data-height=\"{self.__Sizes.height}\""

		return f"<p><img src=\"{self.__MountedPath}\"{Sizes}></p>"

class Paragraph(Header):
	"""Абзац."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CheckText(self, text: str) -> bool:
		"""
		Проверяет, соответствует ли текст требованиям.

		:param text: Проверяемый текст.
		:type text: str
		:return: Возвращает `True`, если текст соответствует требованиям.
		:rtype: bool
		:raise ValueError: Выбрасывается при передаче неверно отформатированного текста.
		:raise UnresolvedTag: Выбрасывается при наличии неразрешённого тега в тексте.
		"""

		if not text: raise ValueError("Text can't be empty.")
		if text.startswith("<p"): raise ValueError("Text must be unwrapped from <p>.")

		Tag = BeautifulSoup(text, "html.parser")

		if Tag.find("img"): raise ValueError("Images must be contained in separated element.")
		self.__ValidateHTML(Tag)

	def __ReplaceLongTags(self, text: str) -> str:
		"""
		Заменяет теги форматирования их короткими версиями.

		:param text: Обрабатываемый текст.
		:type text: str
		:return: Обработанный текст.
		:rtype: str
		"""

		TextHTML = HTML(text)
		TextHTML.replace_tag("em", "i")
		TextHTML.replace_tag("strong", "b")
		TextHTML.replace_tag("strike", "s")
		TextHTML.replace_tag("del", "s")

		return TextHTML.text

	def __ValidateHTML(self, paragraph: BeautifulSoup, exceptions: bool = True) -> BeautifulSoup:
		"""
		Проверяет соответствие абзаца допустимым спецификациям HTML.

		:param paragraph: Проверяемый абзац.
		:type paragraph: BeautifulSoup
		:param exceptions: Указывает, нужно ли выбрасывать соответствующие исключения.
		:type exceptions: bool
		:return: Обработанный абзац.
		:rtype: BeautifulSoup
		:raise UnresolvedTag: Выбрасывается при наличии неразрешённого тега в тексте.
		"""
		
		for Tag in paragraph.find_all():

			if Tag.name not in self.__AllowedTags.keys():
				self.__Logger.error(f"Unresolved tag \"{Tag.name}\".")
				if exceptions: raise Exceptions.UnresolvedTag(Tag)

			else:
				Attributes = Tag.attrs.copy()

				for Attribute in Tag.attrs:
					if Attribute not in self.__AllowedTags[Tag.name]:
						del Attributes[Attribute]
						self.__Logger.warning(f"Unresolved attribute \"{Attribute}\" in \"{Tag.name}\" tag. Removed.")

				Tag.attrs = Attributes

		return paragraph

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Абзац.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self._SystemObjects = system_objects

		self._Text = None
		self._Align = None
		self._Footnotes: list[Footnote] = list()
		self._WrapperTag = "p"

		self.__ParserSettings = self._SystemObjects.manager.current_parser_settings
		self.__Logger = self._SystemObjects.logger

		self.__AllowedTags = {
			"a": ("href"),
			"p": ("align",),
			"b": (),
			"i": (),
			"s": (),
			"u": (),
			"sup": (),
			"sub": ()
		}

	def set_text(self, text: str):
		"""
		Задаёт текст абзаца.

		:param text: Текст абзаца.
		:type text: str
		:param footnotes: Одна или несколько заметок.
		:type footnotes: Footnote | Iterable[Footnote] | None
		:raise ValueError: Выбрасывается при передаче неверно отформатированного текста.
		:raise UnresolvedTag: Выбрасывается при наличии неразрешённого тега в тексте.
		"""

		text = text.strip()
		text = self.__ReplaceLongTags(text)
		self.__CheckText(text)
		if self.__ParserSettings.common.pretty: text = self._PrettyText(text)
		self._Text = text
	
class Blockquote:
	"""Блок текста."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def footnotes(self) -> tuple[Footnote]:
		"""Набор заметок."""

		return tuple(self.__Footnotes)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self):
		"""Блок текста."""

		self.__Elements: list[Paragraph | Image] = list()
		self.__ExtraData: dict[str, str] = dict()
		self.__Footnotes: list[Footnote] = list()

	def add_element(self, element: Paragraph | Image):
		"""
		Добавляет элемент в блок.

		:param element: Добавляемый элемент.
		:type element: Paragraph | Image
		:raises TypeError: Выбрасывается при передаче в качестве аргумента неподдерживаемого объекта.
		"""

		if type(element) not in (Paragraph, Image): raise TypeError("Unsupported element.")

		if type(element) == Paragraph:
			for Note in element.footnotes: self.__Footnotes.append(Note)

		self.__Elements.append(element)

	def add_extra_data(self, key: str, value: str):
		"""
		Добавляет атрибут с данными к блоку в формате `data-{key}="{value}"`.

		:param key: Ключ атрибута.
		:type key: str
		:param value: Значение атрибута.
		:type value: str
		"""

		self.__ExtraData[key] = value

	def to_html(self, footnotes_offset: int | None = None) -> str | None:
		"""
		Возращает HTML представление блока.

		:param footnotes_offset: Сдвиг для индексации заметок. При отсутствии нумерация с нуля.
		:type footnotes_offset: int | None
		:return: HTML представление блока.
		:rtype: str
		"""

		Content = ""
		for Element in self.__Elements:

			if type(Element) == Paragraph:
				Content += Element.to_html(footnotes_offset)
				for _ in Element.footnotes: footnotes_offset += 1

			else: Content += Element.to_html()

		ExtraData = list()
		for Key, Value in self.__ExtraData.items():
			ExtraData.append(f"data-{Key}=\"{Value}\"")
		ExtraData = " ".join(ExtraData)
		if ExtraData: ExtraData = f" {ExtraData}"

		return f"<p><blockquote{ExtraData}>{Content}</blockquote></p>"