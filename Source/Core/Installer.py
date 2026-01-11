from dublib.Methods.Filesystem import ListDir
from dublib.CLI.TextStyler.FastStyler import FastStyler
from dublib.Engine.Patcher import Patch

from typing import TYPE_CHECKING
import shutil
import sys
import os

from dulwich import porcelain

if TYPE_CHECKING:
	from Source.Core.SystemObjects import SystemObjects

class Installer:
	"""Оператор установки."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CheckVenv(self, feature: str) -> bool:
		"""
		Проверяет, создано ли вирутальное окружение Python в стандартном каталоге. Если отсутствует, выводит предупреждение.

		:param feature: Описание функционала, для которого требуется наличие виртуального окружения.
		:type feature: str
		:return: Возвращает `True`, если виртуальное окружение создано.
		:rtype: bool
		"""

		if not os.path.exists(".venv"):
			self.__Logger.warning(f"{feature} isn't supported without Python Virtual Enviroment.")
			return False
		
		return True
	
	def __InstallConfig(self, parser: str, extension: str | None = None):
		"""
		Копирует настройки парсера или расширения в каталог конфигураций.

		:param parser: Имя парсера.
		:type parser: str
		:param extension: Имя расширения парсера, если устанавливается его конфигурация.
		:type extension: str | None
		"""

		Title = f"Parser: " + FastStyler(parser).decorate.bold + "."
		if extension: Title += f" Extension: " + FastStyler(extension).decorate.bold + "."

		OriginalPath = f"Parsers/{parser}/settings.json" if not extension else f"Parsers/{parser}/extensions/{extension}/settings.json"
		ConfigsPath = f"Configs/{parser}/settings.json" if not extension else f"Configs/{parser}/extensions/{extension}.json"

		ParserConfigPath = f"Configs/{parser}"
		if not os.path.exists(ParserConfigPath): os.makedirs(ParserConfigPath)
		ExtensionsConfigsPath = f"Configs/{parser}/extensions"
		if extension and not os.path.exists(ExtensionsConfigsPath): os.makedirs(ExtensionsConfigsPath)

		if os.path.exists(OriginalPath):

			if not os.path.exists(ConfigsPath):
				shutil.copy2(OriginalPath, ConfigsPath)
				self.__Logger.info(f"{Title} Config installed.")

			else: self.__Logger.info(f"{Title} Already have configuration. Skipped.")

		else: self.__Logger.info(f"{Title} No default settings.")

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Оператор установки.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__SystemObjects = system_objects

		self.__Logger = self.__SystemObjects.logger

	def alias(self):
		"""Добавляет алиас быстрого запуска в вирутальную среду."""

		if not self.__CheckVenv("Alias"): return
		if not sys.platform.startswith("linux"): self.__Logger.warning("Alias will be installed only for Bash script.", stdout = True)

		Alias = "alias melon=\"python main.py\""
		File = Patch(".venv/bin/activate")

		if Alias not in File.lines:
			File.append_line(0, Alias)
			File.save()
			self.__Logger.info("Alias installed.", stdout = True)

		else: self.__Logger.warning("Alias already installed.", stdout = True)

	def configs(self):
		"""Копирует настройки парсеров и расширений в каталог конфигураций, если таковые ещё не существуют."""

		for Parser in self.__SystemObjects.manager.parsers_names:
			self.__InstallConfig(Parser)

			try:
				for Extension in ListDir(f"Parsers/{Parser}/extensions"): self.__InstallConfig(Parser, Extension)
			except FileNotFoundError: pass

	def releases(self):
		"""Переводит все подмодули парсеров в последний релиз."""

		for Parser in self.__SystemObjects.manager.parsers_names:
			Path = f"Parsers/{Parser}"
			Manifest = self.__SystemObjects.manager.get_parser_manifest(Parser)

			if Manifest.version:
				porcelain.checkout(Path, Manifest.latest_git_tag, force = self.__SystemObjects.FORCE_MODE)
				self.__Logger.info(f"Parser \"{Parser}\" rebased to {Manifest.version} version.")
				
			else: self.__Logger.warning(f"No release tag found for \"{Parser}\" parser.")

	def requirements(self):
		"""Устанавливает зависимости парсеров."""

		if not self.__CheckVenv("Automatic requirements installation"): return

		for Parser in self.__SystemObjects.manager.parsers_names:
			Path = f"Parsers/{Parser}/requirements.txt"
			ParserBold = FastStyler(Parser).decorate.bold

			if os.path.exists(Path):
				self.__Logger.info(f"Installing requirements for {ParserBold}…", stdout = True)
				ExitCode = os.system(f". .venv/bin/activate && pip install -r {Path}")

				if ExitCode == 0: self.__Logger.info(f"Requirements for {ParserBold} installed.", stdout = True)
				else: self.__Logger.info(f"Error occurs during requirements installation for {ParserBold}.", stdout = True)

	def scripts(self):
		"""Выполняет установочные скрипты парсеров."""

		ScriptTypes = {
			"linux": "sh",
			"win32": "bat"
		}

		for Parser in self.__SystemObjects.manager.parsers_names:
			Path = f"Parsers/{Parser}/install." + ScriptTypes[sys.platform]
			ParserBold = FastStyler(Parser).decorate.bold

			if os.path.exists(Path):
				print(f"Running script for {ParserBold}…")
				ExitCode = os.system(f"bash {Path}")

				if ExitCode == 0: self.__Logger.info(f"Script for {ParserBold} done.", stdout = True)
				else: self.__Logger.error(f"Script for {ParserBold} failure.", stdout = True)

			else: self.__Logger.info(f"No {ParserBold} script for this system.", stdout = True)