from .BaseParser import *

from Source.Core.Base.Formats.Ranobe import Chapter, Branch, Ranobe

class RanobeParser(BaseParser):
	"""Базовый парсер ранобэ."""

	def __init__(self, system_objects: "SystemObjects", title: Ranobe | None = None):
		"""
		Базовый парсер ранобэ.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param title: Данные тайтла.
		:type title: Ranobe | None
		"""

		self._Title: Ranobe
		super().__init__(system_objects, title)

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