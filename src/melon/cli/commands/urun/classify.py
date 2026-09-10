from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from .... import utils
from ....core import exceptions
from ...base.templates import BaseParameters
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(BaseParameters):
	"""Параметры, требуемые обработчиком."""

	target: str
	is_output_json: bool
	file_to_write: Path | None
	is_ignore_case: bool

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Генерирует модель команды.
		
		:param model: Шаблон модели команды.
		:type model: Command
		:return: Модель команды.
		:rtype: CommandModel
		"""


		position = model.create_position("VALUE", "Input value to classification.", important = True)
		position.set_argument()

		self._add_json_output_flag()

		model.base.add_flag("-i", aliases = ("--ignorecase",), description = "Ignore characters case in procedures searching.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Process titles classificators."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> Parameters:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: Parameters
		"""

		return Parameters(
			target = entity.get_position_value("VALUE", expected_type = str, important = True),
			is_output_json = entity.check_flag("-j"),
			file_to_write =  entity.get_key_value("--file", expected_type = Path),
			is_ignore_case = entity.check_flag("-i")
		)

	@override
	def _process(self, parameters: Parameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Параметры, требуемые обработчиком.
		:type parameters: Parameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		script_work_dir: Path = self.system_objects.options.CONFIGS_DIR.value / "classificator"
		script_work_dir.mkdir(exist_ok = True)
		
		try:
			classificator = utils.Classificator(script_work_dir)
		except FileNotFoundError as exception_data:
			self.printer.critical(f"Script file \"{exception_data}\" doesn't exists.")
			return False			
		

		executable_lines = classificator.read_script()
		validation_errors = classificator.validate_script(executable_lines)
		
		for error_data in validation_errors:
			self.printer.error(f"[{error_data.line.file.name}:{error_data.line.number}] {error_data.message}")
		
		if validation_errors:
			self.printer.critical("Script failure due to validation errors.")
			return False
		
		try:
			procedures = classificator.parse_operations(executable_lines)
		except exceptions.utils.classificator.ScriptRuntimeError as exception_data:
			self.printer.critical(str(exception_data))
			return False
		
		classification_result = classificator.classify(parameters.target, procedures, ignore_case = parameters.is_ignore_case)
		
		if parameters.is_output_json:
			self.printer.json(classification_result.to_dict())
		else:
			self.printer.templates.classificator.result(classification_result)

		return True
