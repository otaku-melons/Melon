from .BaseParser import *

from ..Formats.Components.Enums import ContentTypes

from Source.Core.Base.Formats.Manga import Chapter, Branch, Manga

class MangaParser(BaseParser):
	"""Базовый парсер манги."""

	@property
	def content_type(self) -> ContentTypes:
		"""Тип контента."""

		return ContentTypes.Ranobe

	def __init__(self, entry_point: "BaseEntryPoint", title: Manga | None = None):
		"""
		Базовый парсер манги.

		:param entry_point: Точка входа в парсер.
		:type entry_point: BaseEntryPoint
		:param title: Данные тайтла.
		:type title: Manga | None
		"""

		self._Title: Manga
		super().__init__(entry_point, title)

	def amend(self, branch: Branch, chapter: Chapter):
		"""
		Дополняет главу дайными о слайдах.

		:param branch: Данные ветви.
		:type branch: Branch
		:param chapter: Данные главы.
		:type chapter: Chapter
		"""

		super().amend(branch, chapter)

	def set_title(self, title: Manga):
		"""
		Задаёт данные тайтла.

		:param title: Данные тайтла.
		:type title: Manga
		"""

		super().set_title(title)