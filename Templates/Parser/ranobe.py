from Source.Core.Base.Formats.Ranobe.Elements import Blockquote, Footnote, Header, Image, Paragraph
from Source.Core.Base.Parsers.Components.ChapterHeaderParser.Ranobe import ChapterHeaderParser
from Source.Core.Base.Formats.BaseFormat import Cover, Statuses
from Source.Core.Base.Parsers.RanobeParser import RanobeParser
from Source.Core.Base.Formats.Ranobe import Branch, Chapter
from Source.Core.Base.Parsers.Components import Functions

class Parser(RanobeParser):
	"""Парсер ранобэ."""

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