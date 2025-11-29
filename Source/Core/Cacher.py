from Source.Core.Base.Formats.Components.Functions import SafelyReadTitleJSON

from dublib.Engine.Bus import ExecutionStatus

from typing import TYPE_CHECKING
import os

if TYPE_CHECKING:
	from Source.Core.SystemObjects import SystemObjects

class Cacher:
	"""Оператор кэширования пар ID-алиас."""

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Оператор кэширования пар ID-алиас.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__Manager = system_objects.manager
		self.__Temper = system_objects.temper

	def cache_parser_output(self, parser_name: str) -> ExecutionStatus:
		"""
		Кэширует пары ID-алиас файлов в выходном каталоге парсера.

		:param parser_name: Имя парсера.
		:type parser_name: str
		:return: Результат кэширования, в котором доступны ключи:

			* _total_ – всего найдено файлов;
			* _in\\_cache_ – из них уже находились в кэше;
			* _cached_ – кэшировано;
			* _errors_ – последовательность имён файлов (без расширения), в которых возникли ошибки.

		:rtype: ExecutionStatus
		"""

		Status = ExecutionStatus()
		Status["total"] = None
		Status["in_cache"] = 0
		Status["cached"] = 0
		Status["errors"] = list()

		ParserSettings = self.__Manager.get_parser_settings(parser_name)
		Files = list()

		if not os.path.exists(ParserSettings.directories.titles): return Status

		for Element in os.scandir(ParserSettings.directories.titles):
			if not Element.is_file() or not Element.name.endswith(".json"): continue
			else: Files.append(Element.name[:-5])

		Files = tuple(Files)
		Status["total"] = len(Files)

		for CurrentFile in Files:

			try:
				Data = SafelyReadTitleJSON(f"{ParserSettings.directories.titles}/{CurrentFile}.json")

				if self.__Temper.shared_data.journal.get_slug_by_id(Data["id"]):
					Status["in_cache"] += 1

				else:
					self.__Temper.shared_data.journal.update(Data["id"], Data["slug"])
					Status["cached"] += 1

			except:
				Status["errors"].append(CurrentFile)
				continue

		Status["errors"] = tuple(Status["errors"])

		return Status