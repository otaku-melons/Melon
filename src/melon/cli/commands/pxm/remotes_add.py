from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableTypes

from ...base import BaseCommandProcessor
from ...base.templates import BaseParameters

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(BaseParameters):
	"""Параметры, требуемые обработчиком."""

	url: str

class CommandProcessor(BaseCommandProcessor[Parameters]):
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

		position = model.create_position("REPOSITORY", "Repository URL.")
		position.set_argument(ValidableTypes.URL)

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Add parser repository."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: PreparedData) -> Parameters:
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
			url = entity.get_position_value("REPOSITORY", expected_type = str, important = True)
		)

	@override
	def _process(self, parameters: Parameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Требуемые параметры.
		:type parameters: Parameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		self.system_objects.manager.repositories.add(parameters.url)

		return True

