import importlib
import sys
from importlib import resources
from typing import TYPE_CHECKING, cast

from dublib.cli.terminalyzer import ModelsGroup, Terminalyzer
from dublib.cli.terminalyzer.helper import Helper

if TYPE_CHECKING:
	from dublib.cli.terminalyzer.parser.entitites import CommandEntity

	from ..core.system_objects import Printer, SystemObjects
	from .base import BaseCommandProcessor

class CommandsOrchestrator:
	"""Оркестратор команд."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def printer(self) -> "Printer":
		"""Оператор вывода."""

		return self.__system_objects.printer

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __build_submodule_name(self, group: str | None, name: str) -> str:
		"""
		Строит имя подмодуля обработчика команд.

		:param group: Имя группы.
		:type group: str | None
		:param name: Имя команды.
		:type name: str
		:return: Имя подмодуля обработчика команд.
		:rtype: str
		"""

		if group is None:
			return name

		return f"{group}_{name}"

	def __get_group(self, name: str | None) -> ModelsGroup:
		"""
		Получает группу для моделей команд. При отсутствии создаёт.

		:param name: Имя группы.
		:type name: str | None
		:return: Группа моделей команд.
		:rtype: ModelsGroup
		"""

		if name not in self.__groups:
			if name:
				self.__groups[name] = ModelsGroup(name.title(), name)

			else:
				self.__groups[name] = ModelsGroup("Other")
				model = self.__groups[name].create_model("help", "Show commands list. Add command to more info.")
				model.base.add_argument()
				model.base.add_argument()
		
		return self.__groups[name]

	def __get_processors_submodules_names(self, module_name: str) -> tuple[str, ...]:
		"""
		Получает список имён доступных обработчиков команд модуля.

		:param module_name: Имя модуля по пути `melon.cli.commands`.
		:type module_name: str
		:return: Последовательность имён доступных модулей обработки команд.
		:rtype: tuple[str, ...]
		"""

		package: str = f"{__package__}.commands.{module_name}"
		commands_submodules_names: list[str] = [
			file.name[:-3]
			for file in resources.files(package).iterdir()
			if file.name.endswith(".py")
		]

		if "_base" in commands_submodules_names:
			commands_submodules_names.remove("_base")

		return tuple(commands_submodules_names)
	
	def __load_processors(self, module_name: str):
		"""
		Загружает обработчики команд из модуля.

		:param module_name: Имя модуля по пути `melon.cli.commands`.
		:type module_name: str
		"""

		self.__processors.clear()
		self.__groups.clear()

		for submodule_name in self.__get_processors_submodules_names(module_name):
			processor_module = importlib.import_module(f"melon.cli.commands.{module_name}.{submodule_name}")

			group_name, _ = self.__parse_processor_submodule_name(submodule_name)
			group = self.__get_group(group_name)

			processor = cast("BaseCommandProcessor", processor_module.CommandProcessor(self.__system_objects, group))
			self.__processors[submodule_name] = processor

	def __parse_processor_submodule_name(self, submodule_name: str) -> tuple[str | None, str]:
		"""
		Разбивает имя подмодуля обработки команды на имя супергруппы и имя команды.

		:param submodule_name: Имя подмодуля обработки команды
		:type submodule_name: str
		:return: Имя супергруппы и имя команды
		:rtype: tuple[str | None, str]
		"""

		if "_" not in submodule_name:
			return (None, submodule_name)

		supergroup, name = submodule_name.split("_", maxsplit = 1)

		return (supergroup, name)

	def __process_help(self, entity: "CommandEntity"):
		"""
		Обрабатывает команду помощи.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		"""

		arguments = entity.arguments

		if arguments:
			identificator: tuple[str, ...] = tuple(str(value) for value in entity.arguments)
			model = self.__terminalyzer.find_model(identificator)

			if not model:
				self.printer.error("Info for command not found.")
				sys.exit(1)

			self.printer.emit(self.__helper.generate_command_info(model))

		else:
			self.printer.emit(self.__helper.generate_groups_list(self.__terminalyzer.groups))

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Базовый обработчик команды.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param group_name: Название группы команд.
		:type group_name: str
		"""

		self.__system_objects: "SystemObjects" = system_objects

		self.__processors: "dict[str, BaseCommandProcessor]" = {}
		self.__groups: dict[str | None, ModelsGroup] = {}
		self.__terminalyzer = Terminalyzer()
		self.__helper = Helper()

	def run(self, module_name: str):
		"""
		Запускает проверку команды по аргументам скрипта.

		:param module_name: Имя используемого модуля команд.
		:type module_name: str
		"""

		self.__load_processors(module_name)
		self.__terminalyzer.set_commands_groups(tuple(self.__groups.values()))

		entity = self.__terminalyzer.parse_parameters()

		if entity is None:
			self.printer.critical("Command not found.")
			self.printer.emit(f"Execute <b>{module_name} help</b> to show commands list.")
			sys.exit(1)

		if entity.model.name == "help":
			self.__process_help(entity)
			return

		submodule_name: str = self.__build_submodule_name(entity.model.group.supergroup, entity.model.name)
		self.__processors[submodule_name].process(entity)
