from Source.Core.Base.Formats.BaseFormat import Cover, Statuses
from Source.Core.Base.Parsers.MangaParser import MangaParser
from Source.Core.Base.Formats.Manga import Branch, Chapter
from Source.Core.Base.Formats.Manga.Elements import Slide

class Parser(MangaParser):
	"""Парсер манги."""

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def amend(self, branch: Branch, chapter: Chapter):
		"""
		Дополняет главу дайными о слайдах.

		:param branch: Данные ветви.
		:type branch: Branch
		:param chapter: Данные главы.
		:type chapter: Chapter
		"""
		
		pass

	def parse(self):
		"""Получает основные данные тайтла."""

		pass

	def postprocessor(self):
		"""Вносит изменения в тайтл непосредственно перед сохранением."""

		pass