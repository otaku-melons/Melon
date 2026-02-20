from .Enums import ChaptersTypes

from dublib.Methods.Data import Zerotify

from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
	from ..Ranobe import Ranobe

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

		return Zerotify(self._Header)

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
			KeywordMatch = re.search(f"\\b{Keyword}\\s*([\\d\\.]+)", self._Header, re.IGNORECASE)

			if KeywordMatch:
				self._Number = KeywordMatch.group(1).rstrip(".")
				break

	def _ExtractVolume(self):
		"""Извлекает номер тома из заголовка."""

		VolumeMatch = re.search(f"\\b{self._WordsDictionary.volume}\\s*(\\d+)[^\\d]?", self._Header, re.IGNORECASE)
		if VolumeMatch: self._Volume = VolumeMatch.group(1)

	def _LeftCutTitle(self, value: str):
		"""
		Обрезает строку с левого конца до переданного значения.

		:param value: Значение, по которому производится разрез.
		:type value: str
		"""

		TitleParts = self._Header.split(value)
		if len(TitleParts) < 2: return
		self._Header = value.join(TitleParts[1:])

	def _LstripTitle(self):
		"""Удаляет из начала строки небуквенные символы за исключением `…`."""

		ChapterStart = str()

		for Character in self._Header:
			if not Character.isalpha(): ChapterStart += Character
			else: break

		self._Header = self._Header[len(ChapterStart):]
		if ChapterStart.count(".") >= 3 or "…" in ChapterStart: self._Header = f"…{self._Header}"

	def _ExtractPart(self):
		"""Пытается извлечь из названия главы номер части и добавить его к номеру главы."""

		if not self._Header: return
		Buffer = ""
		Offset = 0

		for Character in self._Header[::-1]:
			Offset += 1
			if Character.isdigit() or Character in (".",): Buffer += Character
			else: break

		if not Buffer: return

		Buffer = Buffer[::-1].strip(".")
		self._Number = f"{self._Number}.{Buffer}"
		ChapterName = self._Header[:Offset * -1]
		ChapterName = ChapterName.rstrip("()[] ")
		if ChapterName.lower().endswith(self._WordsDictionary.part): ChapterName = ChapterName[:-5]
		ChapterName = ChapterName.rstrip("()[] ")
		self._Header = ChapterName

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

		self._Header = header
		self._Title = title

		self._WordsDictionary = title.words_dictionary

		self._Volume = None
		self._Number = None
		self._Type = None
	
	def __repr__(self) -> str:
		"""Реинтерпретирует экземпляр в строковое представление."""
		
		return f"ChapterData(volume={self.volume}, number={self.number}, type={self.type}, name={self._Header})"
	
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