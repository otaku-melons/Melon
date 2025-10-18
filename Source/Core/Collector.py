from Source.Core.SystemObjects import SystemObjects
from Source.Core.Base.Formats.Components.Structs import By

from dublib.Methods.Filesystem import ReadJSON
from dublib.Methods.Data import ToIterable

from typing import Iterable
import os

class Collector:
	"""Менеджер коллекций."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def slugs(self) -> list[str]:
		"""Список алиасов в коллекции."""

		return self.__Collection

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __ReadCollection(self) -> list[str]:
		"""Читает коллекцию."""

		Collection = list()
		
		if os.path.exists(self.__Path):
			
			with open(self.__Path, "r") as FileReader:
				Buffer = FileReader.read().split("\n")

				for Line in Buffer:
					Line = Line.strip()
					if Line: Collection.append(Line)

		return Collection

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: SystemObjects, merge: bool = True):
		"""
		Менеджер коллекций.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param merge: Указывает, нужно ли читать файл коллекции. По умолчанию `True`.
		:type merge: boolt
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__SystemObjects = system_objects

		self.__Path = f"{system_objects.temper.parser_temp}/Collection.txt"
		self.__Collection = self.__ReadCollection() if merge else list()

	def append(self, slugs: str | Iterable[str]):
		"""
		Добавляет один или несколько алиасов в коллекцию.

		:param slugs: Добавляемые алиасы.
		:type slugs: str | Iterable[str]
		"""

		slugs = ToIterable(slugs)
		self.__Collection += [Slug for Slug in slugs if Slug not in self.__Collection]

	def get_local_identificators(self, identificator_type: By) -> list[int] | list[str]:
		"""
		Сканирует директорию и возвращает список идентификаторов тайтлов.
			identificator_type – тип идентификаторов в спике.
		"""
		
		ParserSettings = self.__SystemObjects.manager.current_parser_settings

		LocalTitles = [Entry.name for Entry in os.scandir(ParserSettings.common.titles_directory) if Entry.is_file() and Entry.name.endswith(".json")]
		Identificators = list()

		for Filename in LocalTitles:

			try:
				if identificator_type == By.Filename:
					Identificators.append(Filename[:-5])

				elif identificator_type in [By.ID, By.Slug]:
					Title = ReadJSON(f"{ParserSettings.common.titles_directory}/{Filename}") 
					Identificators.append(Title[identificator_type.value])

			except KeyError: pass

		return Identificators

	def save(self, sort: bool = False):
		"""
		Сохраняет коллекцию в файл.

		:param sort: Указывает, требуется ли сортировка по алфавиту.
		:type sort: bool
		"""

		self.__Collection = list(set(self.__Collection))
		if sort: self.__Collection = sorted(self.__Collection)

		with open(self.__Path, "w") as FileWriter:
			for Slug in self.__Collection: FileWriter.write(Slug + "\n")

	def from_local(self) -> int:
		"""Сканирует директорию тайтлов и сторит из неё коллекцию."""
		
		LocalTitles = self.get_local_identificators(By.Slug)
		TitlesCount = len(LocalTitles)
		self.append(LocalTitles)

		return TitlesCount