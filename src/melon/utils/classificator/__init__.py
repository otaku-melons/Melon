import shlex
from pathlib import Path
from typing import Callable, Sequence, cast

from dublib.functions.filesystem import text

from ...core import exceptions
from .enums import Cases, ClassificatorsTypes, Directives
from .structs import (
	ClassificationResult,
	ExecutableLine,
	Operation,
	ScriptValidationError,
	WorkData,
)

class Classificator:
	"""Оператор обработки классификаторов."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ ВАЛИДАЦИИ <<<<< #
	#==========================================================================================#

	def __validate_directive(self, line: ExecutableLine) -> list[ScriptValidationError]:
		"""
		Производит валидацию директивы.

		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:return: Список ошибок валидации.
		:rtype: list[ScriptValidationError]
		"""

		ERRORS: list[ScriptValidationError] = []

		if "[" in line.value and "]" not in line.value:
			ERRORS.append(ScriptValidationError(line, "Unclosed values declaration."))
		if "]" in line.value and "[" not in line.value:
			ERRORS.append(ScriptValidationError(line, "Unopened values array."))

		DirectiveElements: list[str] = line.value.split("[", maxsplit = 1)

		Name = DirectiveElements[0][1:].rstrip()

		if Name not in tuple(Element.name for Element in Directives):
			ERRORS.append(ScriptValidationError(line, f"Unknown directive: \"@{Name}\"."))
			return ERRORS
		
		Directive: Directives | None = None

		for Element in Directives:
			if Element.name == Name:
				Directive = Element
				break

		Directive = cast(Directives, Directive)

		ValidationData = Directive.value
		Values = self.__extract_directive_values(line)

		if not Values and not ValidationData.allow_empty:
			ERRORS.append(ScriptValidationError(line, f"Directive \"@{Directive.name}\" must have values."))
		
		if len(Values) > 1 and not ValidationData.allow_list:
			ERRORS.append(ScriptValidationError(line, f"Directive \"@{Directive.name}\" must have only one value."))
		
		if ValidationData.values:
			for Value in Values:
				if Value not in ValidationData.values:
					ERRORS.append(ScriptValidationError(line, f"Unknown value \"{Value}\" for directive \"@{Directive.name}\"."))
				
		return ERRORS
		
	def __validate_operation(self, line: ExecutableLine) -> list[ScriptValidationError]:
		"""
		Производит валидацию операции.

		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:return: Список ошибок валидации.
		:rtype: list[ScriptValidationError]
		"""

		ERRORS: list[ScriptValidationError] = []
		
		OperationString: str = line.value.lstrip("*").lstrip()
		OperationParts: tuple[str, ...] = tuple(shlex.split(OperationString))

		if len(OperationParts) == 2:
			
			if OperationParts[1] not in ("-", ">"):
				Operator: str = OperationParts[1]
				ERRORS.append(ScriptValidationError(line, f"Unknown operator: \"{Operator}\"."))
			
			if OperationParts[1] == ">":
				ERRORS.append(ScriptValidationError(line, "Renaming operator requires value."))
		
		elif len(OperationParts) == 3:

			if OperationParts[1] != ">":
				ERRORS.append(ScriptValidationError(line, "Only renaming operator supports two values."))
			
		return ERRORS

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ ОБРАБОТКИ ДИРЕКТИВ <<<<< #
	#==========================================================================================#

	def __process_directive_case(self, work_data: WorkData, line: ExecutableLine):
		"""
		Обрабатывает директиву: `@CASE`.

		:param work_data: Данные процесса обработки скрипта.
		:type work_data: WorkData
		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:raises ScriptRuntimeError: Неизвестное значение директивы.
		"""

		value = self.__extract_directive_values(line)[0]

		try:
			work_data.current_case = Cases(value)
		except ValueError:
			raise exceptions.utils.classificator.ScriptRuntimeError(line, f"Unknown case value: \"{value}\".")

	def __process_directive_delete(self, work_data: WorkData, line: ExecutableLine):  # noqa: ARG002
		"""
		Обрабатывает директиву: `@DELETE`.

		:param work_data: Данные процесса обработки скрипта.
		:type work_data: WorkData
		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		"""

		work_data.is_delete = True

	def __process_directive_drop(self, work_data: WorkData, line: ExecutableLine):
		"""
		Обрабатывает директиву: `@DROP`.

		:param work_data: Данные процесса обработки скрипта.
		:type work_data: WorkData
		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:raises ScriptRuntimeError: Неизвестное значение директивы.
		"""

		values = self.__extract_directive_values(line)

		# По умолчанию сбрасывать все значения.
		if not values:
			values = ("type", "case", "delete")

		for value in values:
			match value:
				case "type": work_data.current_type = None
				case "case": work_data.current_case = None
				case "delete": work_data.is_delete = False
				case _: raise exceptions.utils.classificator.ScriptRuntimeError(line, f"Unknown drop value: \"{value}\".")

	def __process_directive_type(self, work_data: WorkData, line: ExecutableLine):
		"""
		Обрабатывает директиву: `@TYPE`.

		:param work_data: Данные процесса обработки скрипта.
		:type work_data: WorkData
		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:raises ScriptRuntimeError: Неизвестное значение директивы.
		"""

		value = self.__extract_directive_values(line)[0]

		try:
			work_data.current_type = ClassificatorsTypes(value)
		except ValueError:
			raise exceptions.utils.classificator.ScriptRuntimeError(line, f"Unknown type: \"{value}\".")

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __extract_directive_values(self, line: ExecutableLine) -> tuple[str, ...]:
		"""
		Извлекает значения директивы без валидации.

		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:return: Значения директивы.
		:rtype: tuple[str, ...]
		"""

		parts: list[str] = line.value.split("[", maxsplit = 1)

		if len(parts) == 1:
			return ()

		value_string: str = parts[1].rstrip("]")
		value_string_elements: list[str] = value_string.split(",")
		result: list[str] = []

		for element in value_string_elements:
			result.append(element.strip())

		return tuple(result)

	def __include_script(self, line: ExecutableLine) -> list[ExecutableLine]:
		"""
		Обрабатывает директиву `@INCLUDE`.

		:param line: Исполняемая строка скрипта.
		:type line: ExecutableLine
		:return: Список исполняемых строк из включаемого файла.
		:rtype: list[ExecutableLine]
		:raises FileNotFoundError: Включаемый файл скрипта не найден.
		"""

		filename: str = self.__extract_directive_values(line)[0]

		if not filename.endswith(".ini"):
			filename += ".ini"

		script_file: Path = self.__work_directory / filename

		if not script_file.exists():
			raise FileNotFoundError(script_file)

		return self.__read_script_file(script_file, include = False)

	def __read_script_file(self, script_file: Path, include: bool = True) -> list[ExecutableLine]:
		"""
		Считывает исполняемые строки из файла скрипта, фильтруя пустые и комментарии.

		В конец каждого файла автоматически добавляется директива `@DROP` при её отсутствии.

		:param script_file: Путь к файлу скрипта.
		:type script_file: Path
		:param include: Указывает, следует ли обрабатывать директивы `@INCLUDE`.
		:type include: bool
		:return: Список данных исполняемых строк.
		:rtype: list[ExecutableLine]
		:raises IncludeDirectiveDeniedError: Директива `@INCLUDE` запрещена.
		"""

		script_lines: list[str] = text.read(script_file, split = True, strip_level = 2)
		executable_lines: list[ExecutableLine] = []

		for index in range(len(script_lines)):
			line: str = script_lines[index]
			line_number: int = index + 1

			if line.startswith("#"):
				continue

			if line.startswith(f"@{Directives.INCLUDE.name}"):

				if not include:
					raise exceptions.utils.classificator.IncludeDirectiveDeniedError(script_file, line_number)

				buffer = ExecutableLine(script_file, line_number, line)
				executable_lines += self.__include_script(buffer)
				continue

			executable_lines.append(ExecutableLine(script_file, line_number, line))

		# Если в конце файла нет директивы сброса, добавить её.
		if executable_lines and executable_lines[-1].value != "@DROP":
			executable_lines.append(ExecutableLine(script_file, -1, "@DROP"))

		return executable_lines

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, work_directory: Path):
		"""
		Оператор обработки скрипта классификации.

		:param work_directory: Путь к рабочей директории.
		:type work_directory: Path
		"""

		self.__work_directory: Path = work_directory
		self.__main_file: Path = work_directory / "main.ini"

		if not self.__main_file.exists():
			raise FileNotFoundError(self.__main_file)

	def classify(self, target: str, procedures: Sequence[Operation], ignore_case: bool = False) -> ClassificationResult:
		"""
		Обрабатывает классификатор.

		:param target: Цель для обработки.
		:type target: str
		:param procedures: Набор операций.
		:type procedures: Sequence[Operation]
		:param ignore_case: Указывает, нужно ли игнорировать регистр.
		:type ignore_case: bool
		:return: Результат обработки.
		:rtype: ClassificationResult
		"""

		operations_cashe: dict[str, Operation] = {}

		if ignore_case:
			operations_cashe = {CurrentProcedure.name.lower(): CurrentProcedure for CurrentProcedure in procedures}
		else:
			operations_cashe = {CurrentProcedure.name: CurrentProcedure for CurrentProcedure in procedures}
		
		target_operation: Operation | None = operations_cashe.get(target.lower() if ignore_case else target)
		if not target_operation: return ClassificationResult()

		name: str | None = target_operation.process(target)
		is_renamed: bool | None = not target == name
		if target_operation.delete: is_renamed = None

		return ClassificationResult(
			is_operation_found = True,
			name = name,
			type = target_operation.type,
			delete = target_operation.delete,
			is_renamed = is_renamed
		)

	def parse_operations(self, script_lines: Sequence[ExecutableLine]) -> tuple[Operation, ...]:
		"""
		Парсит операции обработки классификаторов.

		:param script_lines: Последовательность исполняемых строк скрипта.
		:type script_lines: Sequence[ExecutableLine]
		:return: Последовательность операций обработки классификаторов.
		:rtype: tuple[Operation, ...]
		"""

		operations: list[Operation] = []
		work_data = WorkData()

		directive_processors: dict[Directives, Callable] = {
			Directives.DROP: self.__process_directive_drop,
			Directives.CASE: self.__process_directive_case,
			Directives.DELETE: self.__process_directive_delete,
			Directives.TYPE: self.__process_directive_type
		}

		for line in script_lines:
			
			if line.is_operation:
				operation_line: str = line.value[1:]
				parts: list[str] = shlex.split(operation_line)
				rename: str | None = None

				if len(parts) == 3 and parts[1] == ">":
					rename = parts[2]

				operations.append(Operation(
					name = parts[0],
					type = work_data.current_type,
					delete = work_data.is_delete,
					rename = rename,
					case = work_data.current_case
				))

				continue

			for directive in Directives:
				if line.is_directive(directive):
					directive_processors[directive](work_data, line)

		return tuple(operations)

	def read_script(self) -> tuple[ExecutableLine, ...]:
		"""
		Считывает строки операций из файла скрипта, фильтруя пустые строки и комментарии.

		:return: Последовательность исполняемых строк скрипта.
		:rtype: tuple[ExecutableLine, ...]
		"""

		return tuple(self.__read_script_file(self.__main_file))

	def validate_script(self, script_lines: Sequence[ExecutableLine]) -> tuple[ScriptValidationError, ...]:
		"""
		Производит построчную валидацию скрипта.

		:param script_lines: Последовательность исполняемых строк скрипта.
		:type script_lines: Sequence[ExecutableLine]
		:return: Список ошибок валидации.
		:rtype: tuple[ScriptValidationError, ...]
		"""

		errors: list[ScriptValidationError] = []

		for line in script_lines:
			if line.is_directive(): errors += self.__validate_directive(line)
			elif line.is_operation: errors += self.__validate_operation(line)
			else: errors.append(ScriptValidationError(line, "Unknown string assignment."))
			
		return tuple(errors)
