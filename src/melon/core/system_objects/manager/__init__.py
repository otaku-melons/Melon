import shutil
import subprocess
from typing import TYPE_CHECKING

from .packager import Packager
from .parsers import Parsers
from .repositories import Repositories

if TYPE_CHECKING:
	from .. import SystemObjects

class Manager:
	"""Системный менеджер."""

	@property
	def packager(self) -> Packager:
		"""Пакетный оператор."""

		return self.__Packager

	@property
	def parsers(self) -> Parsers:
		"""Менеджер парсеров."""

		return self.__Parsers

	@property
	def repositories(self) -> Repositories:
		"""Менеджер репозиториев."""

		return self.__Repositories

	@property
	def system_objects(self) -> "SystemObjects":
		"""Коллекция системных объектов."""

		return self.__SystemObjects

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Системный менеджер.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__SystemObjects: "SystemObjects" = system_objects

		self.__Packager = Packager(self)
		self.__Parsers = Parsers(self)
		self.__Repositories = Repositories(self)

	def upgrade(self):
		"""Устанавливает пакет Melon из удалённого репозитория."""

		temp_melon_directory = self.system_objects.options.TEMP_DIR.value / ".melon"
		temp_melon_directory.mkdir(exist_ok = True)

		self.packager.clone(temp_melon_directory, self.system_objects.options.REPOS_URL.value)

		try:
			subprocess.run(("uv", "pip", "install", "melon"), check = True)

		finally:
			shutil.rmtree(temp_melon_directory)
