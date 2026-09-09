from typing import TYPE_CHECKING

from dublib.validators import ValidableTypes

from ...base import BaseCommandProcessor

if TYPE_CHECKING:
	from ...base.templates import BaseParameters

class CommandProcessorTemplate[PARAMS: "BaseParameters"](BaseCommandProcessor[PARAMS]):
	"""Контейнер шаблонов генерации команд."""
	
	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ ГЕНЕРАЦИИ КОМАНДЫ <<<<< #
	#==========================================================================================#

	def _add_mirror_key(self):
		"""Добавляет ключ подключения зеркала."""

		self._model.base.add_key("--mirror", value_type = ValidableTypes.Domain, description = "Source mirror to requests.")
