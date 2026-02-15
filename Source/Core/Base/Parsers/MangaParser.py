from .BaseParser import *

from Source.Core.Base.Formats.Manga import Chapter, Branch, Manga

class MangaParser(BaseParser):
	"""Базовый парсер манги."""

	def __init__(self, system_objects: "SystemObjects", title: Manga | None = None):
		"""
		Базовый парсер манги.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param title: Данные тайтла.
		:type title: Manga | None
		"""

		self._Title: Manga
		super().__init__(system_objects, title)

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

		self._Title = title