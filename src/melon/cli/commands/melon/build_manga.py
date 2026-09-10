from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast, override

from dublib.validators import ValidableTypes

from ....builders.manga import MangaBuilder, MangaOutputFormats
from ....core import exceptions
from ....core.base.formats.base_format.enums import By
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	filename: str
	target_id: int | None
	target_type: Literal["branch", "chapter"] | None
	output_format: str | None
	chapter_template: str | None
	volume_template: str | None
	is_sort_by_volumes: bool

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

		position = model.create_position("FILE", "Filename of local JSON.", important = True)
		position.set_argument()

		self._add_parser_position(key = "--use")

		position = model.create_position("TARGET", "Target for building. By default longest branch.")
		position.add_key("--branch", value_type = ValidableTypes.UnsignedInteger, description = "Branch ID.")
		position.add_key("--chapter", value_type = ValidableTypes.UnsignedInteger, description = "Chapter ID.")

		position = model.create_position("FORMAT", "Format of output content. By default downloads images in folder.")
		position.add_flag("-cbz", description = "Make *.CBZ files.")
		position.add_flag("-pdf", description = "Make *.PDF file.")
		position.add_flag("-zip", description = "Make *.ZIP archives.")

		model.base.add_flag("-s", description = "Enable chapters sorting by volumes directories.")

		model.base.add_key("--cnt", description = "Template for chapters naming.")
		model.base.add_key("--vnt", description = "Template for volumes naming.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Build read-ready manga content."

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
	
		target_type: Literal["branch", "chapter"] | None = None
		if entity.check_key("--chapter"): target_type = "chapter"
		elif entity.check_key("--branch"): target_type = "branch"
	
		output_format: str | None = entity.get_position_value("FORMAT", expected_type = str)
		if output_format: output_format = output_format.lstrip("-")

		return Parameters(
			filename = entity.get_position_value("FILE", expected_type = str, important = True),
			required_parser = prepared_data.required_parsers[0],
			target_id = entity.get_position_value("TARGET", expected_type = int),
			target_type = target_type,
			output_format = output_format,
			chapter_template = entity.get_key_value("--ct", expected_type = str),
			volume_template = entity.get_key_value("--vt", expected_type = str),
			is_sort_by_volumes = entity.check_flag("-s")
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

		source_operator = self._launch_source_operator(parameters.required_parser)
		typing_result = source_operator.get_content_type_by_file(parameters.filename)

		if not typing_result.slug:
			raise exceptions.builders.BuildingError("Undefined title slug.")

		Parser = source_operator.launch_parser(typing_result.content_type)
		Title = Parser.init_empty_title(typing_result.slug)
	
		if Title.load(parameters.filename, By.Filename):
			self.printer.emit(f"Loaded file: <i>{parameters.filename}</i>.")
		else:
			self.printer.error(f"Unable load file: <b>{parameters.filename}</b>.")
			return False
	
		Builder = MangaBuilder(Parser, Title)
		if parameters.output_format: Builder.select_output_format(MangaOutputFormats(parameters.output_format))
		if parameters.chapter_template: Builder.set_chapter_name_template(parameters.chapter_template)
		if parameters.chapter_template: Builder.set_volume_name_template(parameters.chapter_template)
		Builder.switch_volumes_sorting(parameters.is_sort_by_volumes)
	
		match parameters.target_type:
			case "branch": Builder.build_branch(parameters.target_id)
			case "chapter": Builder.build_chapter(cast("int", parameters.target_id))
			case _: Builder.build_branch()

		return True
