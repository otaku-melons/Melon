from typing import TYPE_CHECKING

from ...base import BaseCommandProcessor

if TYPE_CHECKING:
	from ...base.templates import BaseParameters

class CommandProcessorTemplate[PARAMS: "BaseParameters"](BaseCommandProcessor[PARAMS]):
	"""Контейнер шаблонов генерации команд."""
	
	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ ГЕНЕРАЦИИ КОМАНДЫ <<<<< #
	#==========================================================================================#

	def _add_settings_export_strategy_position(self):
		"""Добавляет позицию стратегии слияния конфигурации."""

		position = self._model.create_position("STRATEGY", "Strategy of config installation conflict resolution.")
		position.add_flag("-s", description = "Skip installation (default).")
		position.add_flag("-o", description = "Overwrite exists config.")
		position.add_flag("-m", description = "Merge exists config parameters with preset.")
