from Source.Core.Base.Formats.Components.Structs import ContentTypes
from Source.Core.Base.Parsers.Components.Settings import Settings
from Source.Core.SystemObjects import SystemObjects
from Source.Core.Timer import Timer

from dublib.Methods.Filesystem import WriteJSON
from dublib.CLI.TextStyler.FastStyler import FastStyler
from dublib.Engine.Patcher import Patch

from pathlib import Path
import shutil
import os

class DevelopmeptAssistant:
	"""Ассистент разработчика."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CheckExtensionName(self, name: str) -> bool:
		"""
		Проверяет валидность имени расширения.
			name – имя расширения.
		"""

		if name.count("-") != 1:
			self.__Logger.error("Extension name must have a format \"{PARSER}-{EXTENSION}\".")
			return False
		
		Parser, Extension = name.split("-")

		if not os.path.exists(f"Parsers/{Parser}"):
			self.__Logger.error(f"Parser \"{Parser}\" not found.", stdout = True)
			return False
		
		if os.path.exists(f"Parsers/{Parser}/extensions/{name}"):
			self.__Logger.error(f"Extension \"{name}\" already exists.", stdout = True)
			return False
		
		return True

	def __InitGit(self, path: str):
		"""
		Инициализирует репозиторий Git.
			path – путь к репозиторию.
		"""

		ExitCode = os.system(f"cd {path} && git init -q")
		if ExitCode == 0: self.__Logger.info("Git repository initialized.", stdout = True)
		else: self.__Logger.error("Unable initialize Git repository.", stdout = True)

	def __InsertModuleName(self, path: str, files: str | tuple[str], module: str):
		"""
		Заполняет определение имени парсера.
			path – путь к домашнему каталогу парсера;\n
			files – кортеж файлов для замены;\n
			module – название парсера.
		"""

		if type(files) == str: files = [files]

		for File in files:
			File = Patch(f"{path}/{File}")
			File.replace("NAME = None", f"NAME = \"{module}\"")
			File.replace("{NAME}", module)
			File.save()

	def __IntallFiles(self, files: dict, path: str):
		"""
		Устанавливает файлы в целевой каталог.

		:param files: Словарь устанавливаемых файлов, где ключ это путь к шаблону, а значение – имя файла.
		:type files: dict
		:param path: Путь к каталогу, в который выполняется установка.
		:type path: str
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
		self.__Logger.info(f"Initializing extension {BoldName}...")
		os.makedirs(Path)
		
		try:
			self.__InitGit(Path)
			Files = {
				".gitignore": None,
				"Extension/README.md": None,
				"Extension/main.py": None,
				"Extension/manifest.json": None
			}
			self.__IntallFiles(Files, Path)
			WriteJSON(f"{Path}/settings.json", dict())
			print("File " + FastStyler("settings.json").decorate.italic + " installed.")
			self.__InsertModuleName(Path, "README.md", name)

		except Exception as ExceptionData: 
			shutil.rmtree(Path)
			self.__Logger.error(str(ExceptionData))

		else: TimerObject.done()

	def init_parser(self, name: str, type: ContentTypes):
		"""
		Инициализирует новый репозиторий расширения.

		:param name: Имя парсера.
		:type name: str
		:param type: Тип контента.
		:type type: ContentTypes
		"""

		TimerObject = Timer(start = True)
		Path = f"Parsers/{name}"
		BoldName = FastStyler(name).decorate.bold
		self.__Logger.info(f"Initializing parser {BoldName}...", stdout = True)

		if os.path.exists(Path):
			self.__Logger.error("Parser with this name already exists.", stdout = True)
			return
		
		else: os.makedirs(Path)
		
		try:
			self.__InitGit(Path)
			TypeDirectory = type.value.title()
			Files = {
				".gitignore": None,
				"Parser/README.md": None,
				f"Parser/{TypeDirectory}/main.py": None,
				f"Parser/{TypeDirectory}/manifest.json": None
			}
			self.__IntallFiles(Files, Path)
			WriteJSON(f"{Path}/settings.json", Settings.copy())
			print("File " + FastStyler("settings.json").decorate.italic + " installed.")
			self.__InsertModuleName(Path, ("main.py", "README.md"), name)

		except Exception as ExceptionData: 
			shutil.rmtree(Path)
			self.__Logger.error(str(ExceptionData), stdout = True)

		else: TimerObject.done()