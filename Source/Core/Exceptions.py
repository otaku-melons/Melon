from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseTitle

#==========================================================================================#
# >>>>> ИСКЛЮЧЕНИЯ ПАРСЕРОВ <<<<< #
#==========================================================================================#
	
class BadSettings(Exception):
	"""Исключение: неверно определены настройки парсера."""

	def __init__(self, parser_name: str):
		"""
		Исключение: неверно определены настройки парсера.

		:param parser_name: Имя парсера.
		:type parser_name: str
		"""

		super().__init__(f"Error during parsing \"{parser_name}\" settings.") 

class ChapterNotFound(Exception):
	"""Исключение: глава не найдена."""

	def __init__(self, chapter: "BaseChapter"):
		"""
		Исключение: глава не найдена.

		:param chapter: Данные главы.
		:type chapter: BaseChaptert
		"""

		ChapterIdentificator = ""
		if chapter.id: ChapterIdentificator = f" {chapter.id}"
		elif chapter.slug: ChapterIdentificator = f" \"{chapter.slug}\""

		super().__init__(f"Chapter{ChapterIdentificator} not found.") 
	
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

		super().__init__(description or "Unable get data.") 

class TitleNotFound(Exception):
	"""Исключение: тайтл не найден в источнике."""

	def __init__(self, title: "BaseTitle"):
		"""
		Исключение: тайтл не найден в источнике.

		:param title: Данные тайтла.
		:type title: BaseTitle
		"""

		super().__init__(f"Title \"{title.slug}\" not found.") 
	
class UnsupportedFormat(Exception):
	"""Исключение: неподдерживаемый формат JSON."""

	def __init__(self, format: str | None = None):
		"""
		Исключение: неподдерживаемый формат JSON.

		:param format: Название формата.
		:type format: str | None
		"""

		format = f" \"{format}\"" if format else ""
		super().__init__(f"Unsupported format{format}.") 

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

		super().__init__(f"Unresolved tag \"{tag}\".") 
	
#==========================================================================================#
# >>>>> СИСТЕМНЫЕ ИСКЛЮЧЕНИЯ <<<<< #
#==========================================================================================#

class TempOwnerNotSpecified(Exception):
	"""Исключение: владалец временного каталога не определён."""

	def __init__(self):
		"""Исключение: владалец временного каталога не определён."""

		super().__init__("Parser or extension not specified for temper. Unable to load directory.") 
	
class BadManifest(Exception):
	"""Исключение: неверное определение манифеста."""

	def __init__(self, message: str):
		"""
		Исключение: неверное определение манифеста.

		:param message: Сообщение об ошибке.
		:type message: str
		"""

		super().__init__(message) 