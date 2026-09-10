import os
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import cv2
import numpy
from PIL import Image

from .structs import TemplateMatch

if TYPE_CHECKING:
	from ...core.system_objects import SystemObjects

class Cutter:
	"""Инструмент для вырезания рекламы из слайдов манги."""

	def __cut_template(self, image: cv2.typing.MatLike, template_match: TemplateMatch) -> numpy.ndarray:
		"""
		Вырезает шаблон из изображения.

		:param image: Математическое представление изображения.
		:type image: cv2.typing.MatLike
		:param template_match: Результат поиска шаблона в изображении.
		:type template_match: TemplateMatch
		:return: Математическое представление изображения.
		:rtype: numpy.ndarray
		"""

		image_height: float = image.shape[0]
		top_part: cv2.typing.MatLike = image[0:template_match.start, :]
		bottom_part: cv2.typing.MatLike = image[template_match.end:image_height, :]

		return numpy.vstack((top_part, bottom_part))

	def __is_image_contains_template(self, image: cv2.typing.MatLike, template: cv2.typing.MatLike, threshold: float = 0.8) -> TemplateMatch | None:
		"""
		Проверяет, содержит ли изображение шаблон.

		:param image: Математическое представление изображения.
		:type image: MatLike
		:param template: Математическое представление шаблона.
		:type template: MatLike
		:param threshold: Степень сходства.
		:type threshold: float
		:return: Возвращает 
		:rtype: bool
		"""

		wb_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		wb_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

		match_result = cv2.matchTemplate(wb_image, wb_template, cv2.TM_CCOEFF_NORMED)
		_, max_threshold, _, location = cv2.minMaxLoc(match_result)

		if max_threshold >= threshold:
			template_start: float = location[1]
			template_height: float = template.shape[0]
			template_end: float = template_start + template_height

			return TemplateMatch(
				threshold = max_threshold,
				start = template_start,
				end = template_end
			)

		return None

	def __load_image(self, image_path: Path) -> cv2.typing.MatLike:
		"""
		Считывает изображение для работы с **cv2**.

		:param image_path: Путь к изображению.
		:type image_path: Path
		:return: Математическое представление изображения.
		:rtype: cv2.typing.MatLike
		:raises FileNotFoundError: Файл не найден.
		"""

		if not image_path.exists():
			raise FileNotFoundError(image_path)

		with Image.open(image_path) as image:
			rgb_image = image.convert("RGB")
			return cv2.cvtColor(numpy.array(rgb_image), cv2.COLOR_RGB2BGR)

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Инструмент для вырезания рекламы из слайдов манги.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__system_objects: "SystemObjects" = system_objects

	def calculate_templates_matches(self, image_path: Path, templates: Sequence[Path], threshold: float = 0.8) -> int:
		"""
		Подсчитвает количество найденных в изображении шаблонов.

		:param image_path: Путь к изображению.
		:type image_path: Path
		:param templates: Последовательность путей к шаблонам.
		:type templates: Sequence[Path]
		:param threshold: Степень сходства.
		:type threshold: float
		:return: Количество найденных шаблонов.
		:rtype: int
		"""

		image = self.__load_image(image_path)
		templates_found: int = 0

		for template_path in templates:
			template = self.__load_image(template_path)

			if self.__is_image_contains_template(image, template, threshold):
				templates_found += 1

		return templates_found

	def clean_image(self, image_path: Path, templates: Sequence[Path], output_path: Path | None = None) -> int:
		"""
		Вырезает из изображения полноширинную вставку по шаблону.

		:param image_path: Путь к изображению.
		:type image_path: Path
		:param templates: Последовательность путей к шаблонам.
		:type templates: Sequence[Path]
		:param output_path: Путь для записи результата. По умолчанию перезаписывает оригинальное изображение.
		:type output_path: Path | None
		:return: Количество вырезанных шаблонов.
		:rtype: int
		"""

		image = self.__load_image(image_path)
		cutted_templates_count: int = 0

		for template_path in templates:
			template = self.__load_image(template_path)

			match_result = self.__is_image_contains_template(image, template)

			if match_result:
				image = self.__cut_template(image, match_result)
				cutted_templates_count += 1

		if not output_path: output_path = image_path
		cv2.imwrite(output_path.as_posix(), image)

		return cutted_templates_count

	def get_templates_from_directory(self, directory: Path) -> tuple[Path, ...]:
		"""
		Получает пути к шаблонам во временной директории парсера: `{TEMP_DIR}/{PARSER}/cutter`.

		:param directory: Путь к директории шаблонов.
		:type directory: Path
		:return: последовательность путей.
		:rtype: tuple[Path, ...]
		"""

		if not directory.exists():
			return ()

		paths: list[Path] = []

		for entry in os.scandir(directory):
			if entry.is_file():
				paths.append(directory / entry.name)

		return tuple(paths)
