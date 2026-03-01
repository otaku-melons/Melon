from .BaseParser import *

from ..Formats.Components.Enums import ContentTypes

from Source.Core.Base.Formats.Ranobe import Chapter, Branch, Ranobe

class RanobeParser(BaseParser):
	"""Базовый парсер ранобэ."""

	@property
	def content_type(self) -> ContentTypes:
		"""Тип контента."""

		return ContentTypes.Manga

	def __init__(self, entry_point: "BaseEntryPoint", title: Ranobe | None = None):
		"""
		Базовый парсер ранобэ.

		:param entry_point: Точка входа в парсер.
		:type entry_point: BaseEntryPoint
		:param title: Данные тайтла.
		:type title: Ranobe | None
		"""

		self._Title: Ranobe
		super().__init__(entry_point, title)

	def amend(self, branch: Branch, chapter: Chapter):
		"""
		Дополняет главу абзацами с контентом.

		:param branch: Данные ветви.
		:type branch: Branch
		:param chapter: Данные главы.
		:type chapter: Chapter
		"""

		super().amend(branch, chapter)

	def set_title(self, title: Ranobe):
		"""
		Задаёт данные тайтла.

		:param title: Данные тайтла.
		:type title: Ranobe
		"""

		super().set_title(title)