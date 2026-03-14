from Source.Core.Base.Formats.Components.Enums import ContentTypes
from Source.Core.Base.Parsers.Components.Manifest import Manifest
from Source.Core.Base.Parsers.Components.Settings import Settings
from Source.Core.SystemObjects import SystemObjects
from Source.Core.Timer import Timer

from dublib.CLI.TextStyler.FastStyler import FastStyler
from dublib.Methods.Filesystem import WriteJSON
from dublib.Methods.Data import ToIterable
from dublib.Engine.Patcher import Patch

from typing import Iterable
from pathlib import Path
from os import PathLike
import shutil
import os

from dulwich.repo import Repo

class DevelopmeptAssistant:
	"""Ассистент разработчика."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CheckExtensionName(self, name: str) -> bool:
		"""
		Проверяет валидность имени расширения.

		:param name: Имя расширения.
		:type name: str
		:return: Возвращает `True` при валидном имени.
		:rtype: bool
		"""

		if name.count("-") != 1:
			self.__Logger.error("Extension name must have a format \"{PARSER}-{EXTENSION}\".")
			return False
		
		Parser, _ = name.split("-")

		if not os.path.exists(f"Parsers/{Parser}"):
			self.__Logger.error(f"Parser \"{Parser}\" not found.")
			return False
		
		if os.path.exists(f"Parsers/{Parser}/extensions/{name}"):
			self.__Logger.error(f"Extension \"{name}\" already exists.")
			return False
		
		return True

	def __InitGitReporitory(self, path: PathLike[str]):
		"""
		Инициализирует Git-репозиторий.

		:param path: Путь к будущему репозиторию.
		:type path: PathLike[str]
		"""

		try:
			Repo.init(path)
			self.__Logger.info("Git repository initialized.")

		except Exception as ExceptionData:
			self.__Logger.error(f"Unable to initialize Git repository due to error: \"{ExceptionData}\".")

	def __InsertModuleName(self, path: PathLike[str], files: str | tuple[str], module: str):
		"""
		Подставляет название модуля в текстовые файлы на место вхождений `{NAME}`.

		:param path: Путь к домашнему каталогу модуля.
		:type path: PathLike[str]
		:param files: Набор названий файлов для замены.
		:type files: str | tuple[str]
		:param module: Название модуля.
		:type module: str
		"""

		files = ToIterable(files)

		for File in files:
			File = Patch(f"{path}/{File}")
			File.replace("{NAME}", module)
			File.save()

	def __InstallFiles(self, files: dict, path: PathLike[str]):
		"""
		Устанавливает файлы в целевой каталог.

		:param files: Словарь устанавливаемых файлов, где ключ это путь к шаблону, а значение – имя файла.
		:type files: dict
		:param path: Путь к каталогу, в который выполняется установка.
		:type path: PathLike[str]
		"""

		for File in files.keys():
			OriginalPath = f"Templates/{File}" 
			Filename = files[File] if files[File] else Path(File).name
			TargetPath = f"{path}/{Filename}"
			shutil.copy(OriginalPath, TargetPath)
			print("File " + FastStyler(Filename).decorate.italic + " installed.")

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: SystemObjects):
		"""
		Ассистент разработчика.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__SystemObjects = system_objects

		self.__Logger = self.__SystemObjects.logger

	def init_extension(self, name: str):
		"""
		Инициализирует новый репозиторий расширения.

		:param name: Имя расширения в формате `{PARSER}-{EXTENSION}`.
		:type name: str
		"""

		TimerObject = Timer(start = True)
		if not self.__CheckExtensionName(name): return 
		Parser = name.split("-")[0]

		Path = f"Parsers/{Parser}/extensions/{name}"
		BoldName = FastStyler(name).decorate.bold
		self.__Logger.info(f"Initializing extension {BoldName}…")
		os.makedirs(Path)
		
		try:
			self.__InitGitReporitory(Path)
			Files = {
				".gitignore": None,
				"Extension/README.md": None,
				"Extension/main.py": None,
				"Extension/manifest.json": None
			}
			self.__InstallFiles(Files, Path)
			WriteJSON(f"{Path}/settings.json", dict())
			print("Settings installed.")
			self.__InsertModuleName(Path, "README.md", name)

		except Exception as ExceptionData: 
			shutil.rmtree(Path)
			self.__Logger.error(str(ExceptionData))

		else: TimerObject.done()

	def init_parser(self, name: str, types: Iterable[ContentTypes], git: bool = False):
		"""
		Инициализирует новый репозиторий расширения.

		:param name: Имя парсера.
		:type name: str
		:param types: Тип контента.
		:type types: Iterable[ContentTypes]
		:param git: Указывает, нужно ли инициализировать новый Git-репозиторий.
		:type git: bool
		"""

		TimerObject = Timer(start = True)
		ParserHomeDirectoryPath = f"Parsers/{name}"
		ParserBoldName = FastStyler(name).decorate.bold
		self.__Logger.info(f"Initializing parser {ParserBoldName}…")

		if os.path.exists(ParserHomeDirectoryPath):

			if self.__SystemObjects.FORCE_MODE:
				shutil.rmtree(ParserHomeDirectoryPath)
				self.__Logger.warning("Directory already exists. Force cleared.")
			
			else:
				self.__Logger.error("Parser with this name already exists.")
				return
		
		os.makedirs(ParserHomeDirectoryPath, exist_ok = True)
		
		try:
			if git: self.__InitGitReporitory(ParserHomeDirectoryPath)
			
			Files = {
				".gitignore": None,
				"Parser/README.md": None,
				f"Parser/main.py": None
			}
			for CurrentType in types: Files[f"Parser/{CurrentType.value}.py"] = None
			self.__InstallFiles(Files, ParserHomeDirectoryPath)

			WriteJSON(f"{ParserHomeDirectoryPath}/settings.json", Settings.copy())
			print("Settings installed.")

			ManifestDict = Manifest.copy()
			ManifestDict["content_types"] = tuple(CurrentType.value for CurrentType in types)
			ManifestDict["version"] = "$last_git_tag"
			ManifestDict["melon_required_version"] = f">={self.__SystemObjects.MELON_VERSION.tag}"
			WriteJSON(f"{ParserHomeDirectoryPath}/manifest.json", ManifestDict)
			print("Manifest installed.")

			self.__InsertModuleName(ParserHomeDirectoryPath, ("main.py", "README.md"), name)

		except Exception as ExceptionData: 
			shutil.rmtree(ParserHomeDirectoryPath)
			self.__Logger.error(str(ExceptionData))

		else: TimerObject.done()

	@staticmethod
	def parse_content_types(data: str) -> tuple[ContentTypes]:
		"""
		Получает последовательность типов контента из строкового представления.

		:param data: Строка из имён типов, раздедённых запятой. Например: `manga,ranobe`.
		:type data: str
		:return: Набор типов контента.
		:rtype: tuple[ContentTypes]
		"""

		Types = list()
		for TypeName in data.split(","): Types.append(ContentTypes(TypeName))

		return tuple(Types)