from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Source.Core.Base.Formats.BaseFormat import BaseTitle

#==========================================================================================#
# >>>>> ИСКЛЮЧЕНИЯ ПАРСЕРОВ <<<<< #
#==========================================================================================#
	
class BadSettings(Exception):
	"""Исключение: неверно определены настройки парсера."""

	def __init__(self, parser_name: str):
		"""
		Исключение: неверно определены настройки парсера.
			parser_name – название парсера.
		"""

		self.__Message = f"Error during parsing \"{parser_name}\" settings."
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message

class ChapterNotFound(Exception):
	"""Исключение: глава не найдена."""

	def __init__(self, chapter_id: int):
		"""
		Исключение: глава не найдена.

		:param chapter_id: ID главы.
		:type chapter_id: int
		"""

		super().__init__(f"Chapter {chapter_id} not found.") 
	
class MergingError(Exception):
	"""Исключение: ошибка слияния контента."""

	def __init__(self, message: str | None = None):
		"""
		Исключение: ошибка слияния контента.

		:param message: Текст альтернативного сообщения об ошибке.
		:type message: str | None
		"""

		super().__init__(message or "Every chapter must have ID. Merging skipped.")

class ParsingError(Exception):
	"""Исключение: ошибка парсинга."""

	def __init__(self, description: str | None = None):
		"""
		Исключение: ошибка парсинга.

		:param description: Описание ошибки.
		:type description: str | None
		"""

		if not description: description = "Unable to get data."
		super().__init__(description) 

class TitleNotFound(Exception):
	"""Исключение: тайтл не найден в источнике."""

	def __init__(self, title: "BaseTitle"):
		"""
		Исключение: тайтл не найден в источнике.
			title – данные тайтла.
		"""

		self.__Message = f"Title \"{title.slug}\" not found."
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message
	
class UnsupportedFormat(Exception):
	"""Исключение: неподдерживаемый формат JSON."""

	def __init__(self, format: str | None = None):
		"""
		Исключение: неподдерживаемый формат JSON.

		:param format: Название формата.
		:type format: str | None
		"""

		format = f" \"{format}\"" if format else ""
		self.__Message = f"Unsupported format{format}."
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message

#==========================================================================================#
# >>>>> ИСКЛЮЧЕНИЯ ФОРМАТИРОВЩИКОВ КОНТЕНТА <<<<< #
#==========================================================================================#
	
class UnresolvedTag(Exception):
	"""Исключение: неразрешённый тег."""

	def __init__(self, tag: str):
		"""
		Исключение: неразрешённый тег.

		:param tag: Имя тега.
		:type tag: str
		"""

		self.__Message = f"Unresolved tag \"{tag}\"."
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message
	
#==========================================================================================#
# >>>>> СИСТЕМНЫЕ ИСКЛЮЧЕНИЯ <<<<< #
#==========================================================================================#

class TempOwnerNotSpecified(Exception):
	"""Исключение: владалец временного каталога не определён."""

	def __init__(self):
		"""Исключение: владалец временного каталога не определён."""

		self.__Message = f"Parser or extension not specified for temper. Unable to load directory."
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message
	
class BadManifest(Exception):
	"""Исключение: неверное определение манифеста."""

	def __init__(self, message: str):
		"""
		Исключение: неверное определение манифеста.

		:param message: Сообщение об ошибке.
		:type message: str
		"""

		self.__Message = message
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message