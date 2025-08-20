from Source.Core.Exceptions import BadManifest

from dublib.Methods.Filesystem import ReadJSON
from dublib.Methods.Data import Zerotify

from types import MappingProxyType
from typing import TYPE_CHECKING

from dulwich.contrib.release_robot import get_current_version, get_recent_tags
from dulwich.errors import NotGitRepository

if TYPE_CHECKING:
	from Source.Core.SystemObjects import SystemObjects

Manifest = MappingProxyType({
	"object": "extension",
	"version": None,
	"melon_required_version": None
})

class ExtensionManifest:
	"""Манифест расширения."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def latest_git_tag(self) -> str | None:
		"""Имя самого свежего тега Git."""

		LatestTag = None
		try: LatestTag = get_recent_tags(f"Parsers/{self.__ParserName}/extensions/{self.__ExtensionName}")[0][0]
		except (TypeError, IndexError): pass
		
		return LatestTag

	@property
	def melon_required_version(self) -> str | None:
		"""Требуемая версия Melon."""
		
		return self.__Data["melon_required_version"]

	@property
	def version(self) -> str | None:
		"""Версия парсера."""

		Version: str | None = self.__Data["version"]

		if Version and Version.startswith("$"):
			
			if Version == "$last_git_tag":
				try: Version = get_current_version(f"Parsers/{self.__ParserName}/extensions/{self.__ParserName}-{self.__ExtensionName}")
				except NotGitRepository: Version = None # Обработать вывод в CLI и логи.
				except TypeError: Version = None

			elif Version.startswith("$from_parser:"):
				Ancestor = Version[13:]
				Version = self.__SystemObjects.manager.get_parser_manifest(Ancestor).version

		return Version

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __Validate(self):
		"""Проверяет валидность манифеста."""
		
		for Key in Manifest:
			if Key not in self.__Data: raise BadManifest(f"Key \"{Key}\" not found.")

		if self.__Data["object"] != "extension": raise BadManifest("Extension manifest required, not other object.")

		self.__Data["version"] = Zerotify(self.__Data["version"])

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", parser_name: str, extension_name: str):
		"""
		Манифест расширения.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param parser_name: Имя парсера.
		:type parser_name: str
		:param extension_name: Имя расширения.
		:type extension_name: str
		"""

		self.__SystemObjects = system_objects
		self.__ParserName = parser_name
		self.__ExtensionName = extension_name

		self.__Data = ReadJSON(f"Parsers/{parser_name}/extensions/{parser_name}-{self.__ExtensionName}/manifest.json")
		self.__Validate()