from dublib.Methods.Data import Zerotify

from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
	from Source.Core.Base.Formats.Manga import Manga

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
	def name(self) -> str | None:
		"""Название главы."""

		return Zerotify(self._Header)

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

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

		#---> Проверка возможности извлечения части.
		#==========================================================================================#
		IsExctractable = False

		# Проверка по соответствию последнего слова заголовка слову идентификатору.
		Parts = tuple(Value.lower() for Value in self._Header.split())
		for Part in Parts[::-1]:
			if Part.isalpha():
				if Part == self._WordsDictionary.part: IsExctractable = True
				break

		# Проверка по наличию скобочки в конце строки.
		if self._Header[:-1] in (")", "]"): IsExctractable = True

		if not IsExctractable: return

		#---> Извлечение части.
		#==========================================================================================#
		for Character in self._Header[::-1]:
			Offset += 1
			if Character.isdigit() or Character in (".",): Buffer += Character
			else: break

		if not Buffer: return

		Buffer = Buffer[::-1].strip(".")
		self._Number = f"{self._Number}.{Buffer}"
		ChapterName = self._Header[:Offset * -1]
		ChapterName = ChapterName.rstrip("()[] ")
		if ChapterName.lower().endswith(self._WordsDictionary.part): ChapterName = ChapterName[:len(self._WordsDictionary.part) * -1]
		ChapterName = ChapterName.rstrip("()[] ")
		self._Header = ChapterName

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЙ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, header: str, title: "Manga"):
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
		self._ExtractNumber()
		if self._Number: self._LeftCutTitle(self._Number)
		self._LstripTitle()

		if self._Title.parser.settings.common.pretty: self._ExtractPart()

		return self