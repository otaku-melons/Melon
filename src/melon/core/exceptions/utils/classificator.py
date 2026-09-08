from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pathlib import Path

	from ....utils.classificator import ExecutableLine

class IncludeDirectiveDeniedError(Exception):
	"""Исключение: директива `@INCLUDE` запрещена."""

	def __init__(self, file: "Path", line: int):
		"""
		Исключение: директива `@INCLUDE` запрещена.

		:param file: Путь к файлу скрипта.
		:type file: Path
		:param line: Номер строки с директивой.
		:type line: int
		"""

		super().__init__(f"File \"{file}\". Line {line}.") 

class ScriptRuntimeError(Exception):
	"""Исключение: ошибка исполнения скрипта."""

	def __init__(self, line: "ExecutableLine", message: str | None = None):
		"""
		Исключение: ошибка исполнения скрипта.

		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:param message: Сообщение об ошибке.
		:type message: str | None
		"""

		Message: str = f"[{line.file.name}:{line.number}]"
		if message: Message += " " + message
		super().__init__(Message) 