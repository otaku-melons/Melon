from Source.Core.Base.Formats.Ranobe.Enums import ChaptersTypes
from .Manga import ChapterHeaderParser as MangaChapterHeaderParser

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Source.Core.Base.Formats.Ranobe import Ranobe

class ChapterHeaderParser(MangaChapterHeaderParser):
	"""Парсер заголовка главы."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def type(self) -> ChaptersTypes | None:
		"""Тип главы."""

		return self._Type

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
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

		LowerHeader = self._Header.lower()

		for ChapterType, Word in Determinations.items():
			if LowerHeader.startswith(Word):
				self._Type = ChapterType
				break

		if not self._Type and self._Number: self._Type = ChaptersTypes.chapter

	def _RemovePartTypers(self):
		"""Удаляет ключевые слова типизации."""

		if not self._Header: return
		Keywords = self._WordsDictionary.keywords
		KeywordsToSkip = (self._WordsDictionary.volume, self._WordsDictionary.chapter)
		Keywords = tuple(Value for Value in Keywords if Value not in KeywordsToSkip)
		LowerTitle = self._Header.lower()

		for Keyword in Keywords:
			if LowerTitle.startswith(Keyword):
				self._Header = self._Header[len(Keyword):]
				self._LstripTitle()
				break

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЙ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, header: str, title: "Ranobe"):
		"""
		Парсер заголовка главы.

		:param header: Заголовок главы.
		:type header: str
		:param words_dictionary: Словарь ключевых слов.
		:type words_dictionary: WordsDictionary
		"""

		super().__init__(header, title)
	
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
		self._RemovePartTypers()

		if self._Title.parser.settings.common.pretty: self._ExtractPart()

		return self