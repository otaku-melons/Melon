from dataclasses import dataclass
from pathlib import Path
from typing import cast

@dataclass(frozen = True)
class ImageResolution:
	"""Разрешение изображения в пикселях."""

	width: int
	height: int

class ImageData:
	"""Данные изображения."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def filename(self) -> str:
		"""Имя файла."""

		return Path(self._Link.split("?", maxsplit = 1)[0]).name

	@property
	def link(self) -> str:
		"""Ссылка на изображение."""

		return self._Link

	@property
	def resolution(self) -> ImageResolution | None:
		"""Разрешение изображения."""

		return self._Resolution

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, link: str):
		"""
		Данные изображения.

		:param link: Ссылка на изображение.
		:type link: str
		"""

		self._Link: str = link

		self._Resolution: ImageResolution | None = None

	def create_resolution(self, width: int | None, height: int | None):
		"""
		Создаёт и устанавливает разрешение изображения. Если одно или оба значения `None`, операция пропускается.

		:param width: Ширина изображения.
		:type width: int | None
		:param height: Высота изображения.
		:type height: int | None
		"""

		if not all((width, height)):
			return

		self.set_resolution(ImageResolution(cast("int", width), cast("int", height)))

	def set_link(self, link: str):
		"""
		Задаёт ссылку.

		:param link: Ссылка на изображение.
		:type link: str
		"""

		self._Link = link

	def set_resolution(self, resolution: ImageResolution | None):
		"""
		Указывает разрешение изображения.

		:param resolution: Разрешение изображения.
		:type resolution: ImageResolution | None
		"""

		self._Resolution = resolution

	def to_dict(self, add_filename: bool = False, sizing: bool = True) -> dict:
		"""
		Возвращает словарное представление объекта.

		:param add_filename: Указывает, нужно ли добавлять ключ с именем файла.
		:type add_filename: bool
		:param sizing: Указывает, нужно ли сохранять ключи с разрешением изображения.
		:type sizing: bool
		:return: Словарное представление объекта.
		:rtype: dict
		"""

		Buffer: dict = {
			"link": self._Link,
			"filename": self.filename,
			"width": self._Resolution.width if self._Resolution else None,
			"height": self._Resolution.height if self._Resolution else None
		}

		if not sizing:
			del Buffer["width"]
			del Buffer["height"]

		if not add_filename:
			del Buffer["filename"]

		return Buffer
