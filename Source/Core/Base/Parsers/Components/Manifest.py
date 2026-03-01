from Source.Core.Base.Formats.Components.Enums import ContentTypes
from Source.Core.Base.Formats.Ranobe import Ranobe
from Source.Core.Base.Formats.Manga import Manga
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
	"object": "parser",
	"site": None,
	"content_types": [],
	"parent": None,
	"version": None,
	"melon_required_version": None
})

class ParserManifest:
	"""Манифест парсера."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def latest_git_tag(self) -> str | None:
		"""Имя самого свежего тега Git."""

		LatestTag = None
		try: LatestTag = get_recent_tags(f"Parsers/{self.__ParserName}")[0][0]
		except (TypeError, IndexError): pass
		
		return LatestTag

	@property
	def name(self) -> str:
		"""Имя парсера."""

		return self.__ParserName

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def site(self) -> str:
		"""Домен сайта."""

		return self.__Data["site"]
	
	@property
	def content_types(self) -> tuple[ContentTypes]:
		"""Типы поддерживаемого контента."""

		return tuple(ContentTypes(Value) for Value in self.__Data["content_types"])
	
	@property
	def parent(self) -> str:
		"""Имя родительского парсера."""

		return self.__Data["parent"]

	@property
	def version(self) -> str | None:
		"""Версия парсера."""

		Version: str | None = self.__Data["version"]

		if Version and Version.startswith("$"):
			
			if Version == "$last_git_tag":
				try: Version = get_current_version(f"Parsers/{self.__ParserName}")
				except NotGitRepository: Version = None # Обработать вывод в CLI и логи.
				except TypeError: Version = None

			elif Version == "$from_parent":
				Version = self.__SystemObjects.manager.get_parser_manifest(self.parent).version

			elif Version.startswith("$from_parser:"):
				Ancestor = Version[13:]
				Version = self.__SystemObjects.manager.get_parser_manifest(Ancestor).version

		return Version

	@property
	def melon_required_version(self) -> str | None:
		"""Требуемая версия Melon."""

		Version: str | None = self.__Data["melon_required_version"]
		if Version == "$from_parent": Version = self.__SystemObjects.manager.get_parser_manifest(self.parent).melon_required_version
		
		return Version

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __Validate(self):
		"""
		Проверяет валидность манифеста.

		:raises BadManifest: Выбрасывается при ошибке валидации манифеста.
		"""
		
		for Key in Manifest:
			if Key not in self.__Data: raise BadManifest(f"Key \"{Key}\" not found.")

		if self.__Data["object"] != "parser": raise BadManifest("Parser manifest required, not other object.")
		if not self.__Data["site"]: raise BadManifest("Site must be specified.")

		if not self.__Data["content_types"]: raise BadManifest("Types must be specified.")
		for ContentType in self.__Data["content_types"]:
			if ContentType not in ("manga", "ranobe", "anime"): raise BadManifest(f"Unsupported content type \"{ContentType}\".")

		for Key in ("version", "melon_required_version"):
			if self.__Data[Key] == "$from_parent" and not self.__Data["parent"]: raise BadManifest("Parent must be specified if using \"$from_parent\".")

		if self.__Data["parent"] and self.__Data["parent"] not in self.__SystemObjects.manager.parsers_names: raise BadManifest("Parent \"" + self.__Data["parent"] + "\" not found.")

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", parser_name: str):
		"""
		Манифест парсера.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param parser_name: Имя парсера.
		:type parser_name: str
		"""
		
		self.__SystemObjects = system_objects
		self.__ParserName = parser_name

		self.__Data = ReadJSON(f"Parsers/{self.__ParserName}/manifest.json")
		self.__Validate()
		self.__Data["version"] = Zerotify(self.__Data["version"])