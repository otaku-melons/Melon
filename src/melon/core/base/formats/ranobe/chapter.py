from typing import Sequence, cast, override

from ..base_format.chapter import BaseChapter
from .elements import Blockquote, Header, Image, Paragraph
from .enums import ChaptersTypes

class Chapter(BaseChapter):
	"""Глава ранобэ."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def footnotes(self) -> tuple[str, ...]:
		"""Последовательность заметок."""

		return tuple(self._data["footnotes"])

	@property
	def paragraphs(self) -> tuple[str, ...]:
		"""Последовательность абзацев."""

		return tuple(self._data["paragraphs"])
	
	@property
	def type(self) -> ChaptersTypes | None:
		"""Тип главы."""

		return ChaptersTypes[self._data["type"]]

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	@override
	def _clear(self):
		"""Очищает контент главы."""

		self._data["paragraphs"] = []
		self._data["footnotes"] = []

	@override
	def _is_empty(self) -> bool:
		"""
		Проверяет, пустая ли глава.

		:return: Состояние: пуста ли глава.
		:rtype: bool
		"""

		return not bool(self._data["paragraphs"])

	@override
	def _from_dict(self, data: dict):
		"""
		Заполняет данные главы из словаря.

		:param data: Словарь данных главы.
		:type data: dict
		"""

		self._data = self._data | data

	@override
	def _post_init(self):
		"""Метод, выполняющийся после инициализации объекта."""

		self._data["paragraphs"] = []
		self._data["footnotes"] = []

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def add_element(self, element: "Paragraph | Image | Header | Blockquote"):
		"""
		Добавляет элемент в главу.

		:param element: Элемент главы.
		:type element: Paragraph | Image | Header | Blockquote
		:raise TypeError: Выбрасывается при передаче неподдерживаемого элемента.
		"""

		if type(element) not in (Paragraph, Image, Header, Blockquote):
			raise TypeError("Unsupported element.")

		if type(element) in (Paragraph, Blockquote, Header):
			element = cast("Paragraph | Blockquote | Header", element)
			self._data["paragraphs"].append(element.to_html(footnotes_offset = len(self.footnotes)))
			for CurrentNote in element.footnotes:
				self._data["footnotes"].append(CurrentNote.to_html())

		else:
			self._data["paragraphs"].append(element.to_html())

	def set_elements(self, elements: "Sequence[Paragraph | Image | Header | Blockquote]"):
		"""
		Задаёт набор элементов главы.

		:param elements: Набор элементов главы.
		:type elements: Sequence[Paragraph | Image | Header | Blockquote]
		"""

		for Element in elements: self.add_element(Element)

	def set_type(self, chapter_type: ChaptersTypes | None):
		"""
		Задаёт тип главы.

		:param chapter_type: Тип главы.
		:type chapter_type: ChaptersTypes | None
		"""

		self._data["type"] = chapter_type.value if chapter_type else None
