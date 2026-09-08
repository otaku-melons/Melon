from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from dublib.functions.filesystem import json
from dublib.validators import ValidableTypes

from .... import utils
from ...base.templates import T_OptionalSingleParser
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ....core.system_objects.manager.parsers import ParserOperator
	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_OptionalSingleParser):
	"""Параметры, требуемые обработчиком."""

	image: Path
	signature_version: utils.unstubber.SignaturesVersions

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __export_signature(self, signature: str, required_parser: "ParserOperator") -> bool:
		"""
		Экспортирует сигнатуру в файл конфигурации парсера.

		:param signature: Сигнатура изображения.
		:type signature: str
		:param required_parser: Оператор парсера.
		:type required_parser: ParserOperator
		:return: Возвращает `False`, если команда требует прерывания выполнения.
		:rtype: bool
		"""

		Config: Path = self.system_objects.options.CONFIGS_DIR.value / f"{required_parser.name}.json"

		if not Config.exists():
			self.printer.emit("Configuration file not found.")
			return False

		ConfigData: dict[str, dict] = json.read(Config)

		if "filters" not in ConfigData: ConfigData["filters"] = {}
		if "images" not in ConfigData["filters"]: ConfigData["filters"]["images"] = {}

		Signatures: list[str] = ConfigData["filters"]["images"].get("signatures", [])

		if signature in Signatures:
			self.printer.warning("Signature already exists. Export skipped.")
			return True

		Signatures.append(signature)
		ConfigData["filters"]["images"]["signatures"] = Signatures
		json.write(Config, ConfigData)
		self.printer.emit(f"Exported in <b>{required_parser.name}</b> config.")

		return True

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

		position = model.create_position("IMAGE", "Path to image.", important = True)
		position.set_argument(ValidableTypes.ValidPath)

		position = model.create_position("VERSION", "Signature version.", important = True)
		position.add_flag("-v1", description = "Based on image sizes and pixels SHA256 hash: exact match.")
		position.add_flag("-v2", description = "Based on perceptual hash: approximate match.")

		self._add_parser_position(key = "--export", description = "Export signature in parser config.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Generate image filtering signature."

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

		version_key: str = entity.get_position_value("VERSION", expected_type = str, important = True)
		version_key = version_key.lstrip("-")
		version = utils.unstubber.SignaturesVersions[version_key]

		return Parameters(
			required_parser = prepared_data.required_parsers[0] if prepared_data.required_parsers else None,
			image = entity.get_position_value("IMAGE", expected_type = Path, important = True),
			signature_version = version
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

		Unstubber = utils.Unstubber()
		Image = Unstubber.load_image(parameters.image)
		Signature: str = Unstubber.generate_signature(Image, parameters.signature_version)
		self.printer.emit(f"Signature: <i>{Signature}</i>")

		if parameters.required_parser:
			return self.__export_signature(Signature, parameters.required_parser)

		return True
