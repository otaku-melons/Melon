from typing import Sequence, cast, override

from ...structs.image import ImageData
from ..base_format.chapter import BaseChapter

class Chapter(BaseChapter):
	"""Глава манги."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def slides(self) -> "tuple[ImageData, ...]":
		"""Последовательность изображений."""

		return tuple(self.__slides.values())
	
	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __get_new_slide_index(self, start_index: int = 1) -> int:
		"""
		Генерирует индекс нового слайда.

		:param start_index: Индекс, с которого начинается нумерация слайдов.
		:type start_index: int
		:return: Индекс слайда.
		:rtype: int
		"""

		indexes: tuple[int, ...] = tuple(self.__slides.keys())

		if not indexes:
			return start_index
		else:
			return max(indexes) + 1

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#
	@override
	def _clear(self):
		"""Очищает контент главы."""

		self.__slides.clear()

	@override
	def _is_empty(self) -> bool:
		"""
		Проверяет, пустая ли глава.

		:return: Состояние: пуста ли глава.
		:rtype: bool
		"""

		return not bool(self.slides)

	@override
	def _from_dict(self, data: dict):
		"""
		Заполняет данные главы из словаря.

		:param data: Словарь данных главы.
		:type data: dict
		"""

		self.clear()
		self._data = self._data | data
		
		for SlideData in self._data["slides"]:
			SlideData = cast("dict", SlideData)
			SlideIndex: int = SlideData["index"]
			SlideImage = ImageData(SlideData["link"])

			Width, Height = SlideData.get("width"), SlideData.get("height")

			if all((Width, Height)):
				SlideImage.create_resolution(Width, Height)

			self.__slides[SlideIndex] = SlideImage

	@override
	def _post_init(self):
		"""Метод, выполняющийся после инициализации объекта."""

		self._data["slides"] = []
		self.__slides: "dict[int, ImageData]" = {}

	@override
	def _pre_formatter(self):
		"""Метод, запускающийся перед генерацией словарного представления объекта."""

		SlidesData: list[dict] = []
		
		for Index, Image in self.__slides.items():
			Buffer: dict = {"index": Index} | Image.to_dict(sizing = self._parser.settings.common.sizing_images)
			SlidesData.append(Buffer)

		self._data["slides"] = tuple(SlidesData)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def add_slide(self, image: "ImageData") -> bool:
		"""
		Добавляет слайд.

		Если для слайда определено разрешение, проверяет его фильтром изображений. В случае провала проверки слайд не добавляется.

		:param image: Данные изображения.
		:type image: ImageData
		:return: Возвращает `True`, если слайд добавлен.
		:rtype: bool
		"""

		if image.resolution and not self._parser.settings.filters.images.check_resolution(image.resolution):
			return False

		index = self.__get_new_slide_index()
		self.__slides[index] = image

		return True
		
	def set_slides(self, images: "Sequence[ImageData]"):
		"""
		Задаёт слайды.

		:param images: Данные изображений.
		:type images: Sequence[ImageData]
		"""

		self.clear()
		
		for current_image in images:
			self.add_slide(current_image)
