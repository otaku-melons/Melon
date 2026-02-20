from Source.Core.Base.Parsers.Components.ImagesDownloader import ImageResolution

from dublib.Methods.Data import Zerotify

from typing import TYPE_CHECKING
from pathlib import Path

import validators

if TYPE_CHECKING:
	from ..Manga import Chapter

	from Source.Core.SystemObjects import SystemObjects

class Slide:
	"""Слайд."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def link(self) -> str:
		"""Ссылка на изображение."""

		return self.__Link
	
	@property
	def resolution(self) -> ImageResolution | None:
		"""Разрешение изображения."""

		return self.__Resolution

	@property
	def type(self) -> str | None:
		"""Расширение изображения в нижнем регистре."""

		return Zerotify(self.__PathObject.suffix.lstrip(".").lower())

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", chapter: "Chapter"):
		"""
		Слайд.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""

		self.__SystemObjects = system_objects
		self.__Chapter = chapter

		self.__ParserSettings = self.__SystemObjects.manager.current_parser_settings

		self.__Link = None
		self.__PathObject = None
		self.__Resolution = None

	def from_dict(self, data: dict):
		"""
		Получает данные слайда из словаря, используя ключи: _link_, _width_, _height_.

		:param data: Словарь данных.
		:type data: dict
		:raise KeyError: Выбрасывается при отсутствии ключа _link_.
		"""

		self.set_link(data["link"])
		Width, Height = data.get("width"), data.get("height")
		if Width and Height: self.set_resolution(Width, Height)

	def set_link(self, link: str) -> "Slide":
		"""
		Задаёт ссылку на изображение.

		:param link: Ссылка на изображение.
		:param type: str
		:raise ValueError: Выбрасывается при передаче некорректного URL.
		:return: Текущий объект слайда.
		:rtype: Slide
		"""

		if not validators.url(link): raise ValueError("Incorrect URL.")
		self.__Link = link
		self.__PathObject = Path(self.__Link)

	def set_resolution(self, width: int, height: int):
		"""
		Указывает разрешение изображения.

		:param width: Ширина изображения.
		:type width: int
		:param height: Высота изображения.
		:type height: int
		"""

		self.__Resolution = ImageResolution(width, height)

	def to_dict(self) -> dict[str, int | str]:
		"""
		Возвращает словарное представление слайда.

		:return: Словарное представление слайда.
		:rtype: dict[str, int | str]
		"""

		Buffer = {
			"index": len(self.__Chapter.slides) + 1,
			"link": self.__Link,
			"width": self.__Resolution.width if self.__Resolution else None,
			"height": self.__Resolution.height if self.__Resolution else None
		}

		if not self.__ParserSettings.common.sizing_images:
			del Buffer["width"]
			del Buffer["height"]

		return Buffer

