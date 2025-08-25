from Source.Core.Base.Formats.Ranobe import Branch, Chapter, ChaptersTypes, Ranobe
from Source.Core.Base.Parsers.RanobeParser import RanobeParser
from Source.Core.Base.Formats.BaseFormat import Statuses

class Parser(RanobeParser):
	"""Парсер."""
	
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

	def amend_postprocessor(self, chapter: Chapter):
		"""
		Вносит изменения в главу после дополнения её контентом. Запускается независимо от процесса дополнения.
		
		Переопределите данный метод для обработки.

		:param chapter: Данные главы.
		:type chapter: Chapter
		"""

		pass
	
	def parse(self):
		"""Получает основные данные тайтла."""

		self._Title

		pass