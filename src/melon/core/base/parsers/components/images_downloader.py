import shutil
from dataclasses import dataclass
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

from .....utils.unstubber import Unstubber
from ...structs.image import ImageResolution

if TYPE_CHECKING:
	from dublib.web_requestor import WebRequestor

	from ...source_operator import BaseSourceOperator

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class FilteredBy(Enum):
	"""Перечисление типов фильтрации."""

	Resolution = 1
	Size = 2
	Signature = 3

@dataclass(frozen = True)
class ImageDownloadingResult:
	"""Результат скачивания изображения."""

	url: str
	is_downloaded: bool
	is_already_exists: bool
	path: Path | None

	filtered_by: FilteredBy | None = None
	resolution: ImageResolution | None = None
	error_message: str | None = None

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class ImagesDownloader:
	"""Оператор загрузки изображений."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def is_custom_requestor_used(self) -> bool:
		"""Состояние: используется ли кастомный оператор запросов."""

		return bool(self.__CustomRequestor)

	@property
	def requestor(self) -> "WebRequestor":
		"""Используемый оператор запросов."""

		return self.__CustomRequestor or self.__Requestor

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, source_operator: "BaseSourceOperator"):
		"""
		Оператор загрузки изображений.

		:param source_operator: Оператор источника.
		:type source_operator: BaseSourceOperator
		"""
		
		self.__SourceOperator = source_operator

		self.__SystemObjects = self.__SourceOperator.system_objects
		self.__Temper = self.__SystemObjects.temper
		self.__ParserSettings = self.__SourceOperator.settings
		self.__Requestor = self.__SourceOperator.requestor
		self.__Unstubber = Unstubber()

		self.__CustomRequestor: "WebRequestor | None" = None

	def build_target_filename(self, url: str, filename: str | None = None, is_full_filename: bool = True) -> str:
		"""
		Строит имя файла на основе URL по заданным параметрам.

		:param url: Ссылка на изображение или псевдоссылка из оригинального имени файла.
		:type url: str
		:param filename: Имя файла. По умолчанию будет сгенерировано на основе URL.
		:type filename: str | none
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:return: Имя файла.
		:rtype: str
		"""

		ParsedUrl = Path(url.split("?", maxsplit = 1)[0])

		if filename:
			if is_full_filename:
				return ParsedUrl.with_name(filename).name
			else:
				return ParsedUrl.with_stem(filename).name
			
		return ParsedUrl.name

	def build_target_path(self, url: str, directory: str | PathLike[str] | None = None, filename: str | None = None, is_full_filename: bool = True) -> Path:
		"""
		Строит целевой путь изображения.

		:param url: Ссылка на изображение.
		:type url: str
		:param directory: Целевая директория. По умолчанию будет проверен временный каталог парсера.
		:type directory: str | PathLike[str] | None
		:param filename: Имя файла. По умолчанию будет сгенерировано на основе URL.
		:type filename: str | none
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:return: Целевой путь изображения.
		:rtype: Path
		"""

		ImageDirectory: Path = Path(directory) if directory else self.__Temper.get_parser_temp_directory(self.__SourceOperator.manifest.parser_name)
		ImagePath = ImageDirectory / self.build_target_filename(url, filename, is_full_filename)

		return ImagePath

	def download_image(self, url: str, directory: str | PathLike[str] | None = None, filename: str | None = None, is_full_filename: bool = False, force_mode: bool = False) -> ImageDownloadingResult:
		"""
		Скачивает изображение.

		:param url: Ссылка на изображение.
		:type url: str
		:param directory: Путь к каталогу, в который нужно сохранить файл. По умолчанию будет использован временный каталог парсера.
		:type directory: str | PathLike[str] | None
		:param filename: Имя файла. По умолчанию будет сгенерировано на основе URL.
		:type filename: str | None
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:param force_mode: Переключает режим перезаписи существующих изображений.
		:type force_mode: bool
		:return: Результат скачивания изображения.
		:rtype: ImageDownloadingResult
		"""

		TempDirectory = self.__Temper.get_parser_temp_directory(self.__SourceOperator.manifest.parser_name)
		ImageDirectory = Path(directory) if directory else TempDirectory
		ImageFilename = self.build_target_filename(url, filename, is_full_filename)
		ImagePath = ImageDirectory / ImageFilename

		IsAlreadyExists: bool = ImagePath.exists()
		Resolution: ImageResolution | None = None
		IsFiltered: FilteredBy | None = None
		IsDownloaded: bool = False
		ErrorMessage: str | None = None

		#---> Проверка кэша отфильтрованных изображений.
		#==========================================================================================#
		IsFiltered = self.__SourceOperator.shared_data.filtered_images.check(url)
		if IsFiltered:
			return ImageDownloadingResult(
				url = url,
				is_already_exists = False,
				is_downloaded = False,
				filtered_by = IsFiltered,
				path = None
			)

		#---> Подстановка доменов зеркал.
		#==========================================================================================#
		ImagesMirrors: dict[str, str] = self.__SourceOperator.settings.network.images_mirrors
		if ImagesMirrors:
			url = self.replace_url_domain(url, ImagesMirrors)

		#---> Скачивание файла.
		#==========================================================================================#
		if not IsAlreadyExists or force_mode:
			Response = self.requestor.get(url)

			if Response.ok and Response.content:
				Resolution = self.get_image_resolution(Response.content)
				IsFiltered = self.filter_image(Response.content, Resolution)
				
				if IsFiltered is None:
					with open(ImagePath, "wb") as FileWriter:
						FileWriter.write(Response.content)
						IsDownloaded = True

				else: self.__SourceOperator.shared_data.filtered_images.add(url, IsFiltered)

			else: ErrorMessage = f"Response code: {Response.status_code}."

		return ImageDownloadingResult(
			url = url,
			is_already_exists = IsAlreadyExists,
			is_downloaded = IsDownloaded,
			filtered_by = IsFiltered,
			resolution = Resolution,
			path = ImagePath,
			error_message = ErrorMessage
		)

	def filter_image(self, image: bytes, resolution: ImageResolution | None) -> FilteredBy | None:
		"""
		Проверяет изображение фильтрами.

		:param image: Бинарное представление изображения.
		:type image: bytes
		:param resolution: Разрешение изображения в пикселях.
		:type resolution: ImageResolution | None
		:return: Возвращает причину фильтрации.
		:rtype: FilteredBy | None
		"""

		if resolution and not self.__SourceOperator.settings.filters.images.check_resolution(resolution):
			return FilteredBy.Resolution

		MinImageSize = self.__SourceOperator.settings.filters.images.min_size		
		if len(image) < MinImageSize:
			return FilteredBy.Size

		Signatures = self.__SourceOperator.settings.filters.images.signatures
		if Signatures:
			Image = self.__Unstubber.build_image(image)

			if self.__Unstubber.filter_image(Image, Signatures):
				return FilteredBy.Signature

		return None

	def get_image_resolution(self, data: bytes) -> ImageResolution | None:
		"""
		Вычисляется на основе бинарного представления разрешение изображения.

		:return: Разрешение изображения или `None` при ошибке вычисления или отключении получения размера настройками парсера.
		:rtype: ImageResolution | None
		"""

		if not self.__ParserSettings.common.sizing_images:
			return None
		
		if not data:
			return None

		Resolution = None

		try:
			Buffer = self.__Unstubber.build_image(data)
			Resolution = ImageResolution(Buffer.size[0], Buffer.size[1])
		except Exception:
			return None

		return Resolution
	
	def move_from_temp(self, directory: str | PathLike[str], original_filename: str, filename: str | None = None, is_full_filename: bool = True, force_mode: bool = False) -> Path:
		"""
		Перемещает изображение из временного каталога парсера в друкгую директорию.

		Если в целевой директории уже существует файл с таким именем, в зависимости от состояния режима перезаписи он будет или перезаписан, или временный файл будет удалён.

		:param directory: Целевая директория.
		:type directory: str | PathLike[str]
		:param original_filename: Имя файла во временном каталоге парсера.
		:type original_filename: str
		:param filename: Новое имя файла. По умолчанию будет использовано оригинальное.
		:type filename: str | None
		:param is_full_filename: Указывает, является ли новое имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе оригинального имени), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:return: Путь к изображению после перемещения.
		:rtype: Path
		:param force_mode: Переключает режим перезаписи существующих изображений.
		:type force_mode: bool
		:raises FileNotFoundError: Не найден оригинальный файл.
		"""

		ImageOriginalDirectory = self.__Temper.get_parser_temp_directory(self.__SourceOperator.manifest.parser_name)
		ImageOriginalFilename = original_filename
		ImageOriginalPath = ImageOriginalDirectory / ImageOriginalFilename

		ImageTargetDirectory = Path(directory)
		ImageTargetFilename = self.build_target_filename(original_filename, filename, is_full_filename)
		ImageTargetPath = ImageTargetDirectory / ImageTargetFilename

		if not ImageOriginalPath.exists():
			raise FileNotFoundError(ImageOriginalPath)

		if ImageTargetPath.exists() and force_mode:
			ImageTargetPath.unlink()

		shutil.move(ImageOriginalPath, ImageTargetPath)

		return ImageTargetPath
	
	def replace_url_domain(self, url: str, rules: dict[str, str] | None = None) -> str:
		"""
		Заменяет домен в ссылке по набору правил.

		:param url: Ссылка.
		:type url: str
		:param rules: Словарь правил, где ключ – заменяемый домен, а значение – подставляемый.
		:type rules: dict[str, str] | None
		:return: Изменённая ссылка или оригинальная, если правила не сработали.
		:rtype: str
		"""

		if rules is None:
			rules = self.__SourceOperator.settings.network.images_mirrors

		ParsedURL = urlparse(url)
		Domain: str = ParsedURL.netloc

		if Domain in rules:
			ParsedURL = ParsedURL._replace(netloc = rules[Domain])

		return urlunparse(ParsedURL)

	def set_requestor(self, requestor: "WebRequestor | None"):
		"""
		Задаёт иной оператор запросов, подменяющий собой предоставляемый оператором источника.

		:param requestor: Собственный оператор запросов или `None` для отключения подмены.
		:type requestor: WebRequestor | None
		"""

		self.__CustomRequestor = requestor

	def temp_image(self, url: str, filename: str | None = None, is_full_filename: bool = False, force_mode: bool = False) -> ImageDownloadingResult:
		"""
		Скачивает изображение во временный каталог парсера..

		:param url: Ссылка на изображение.
		:type url: str
		:param filename: Имя файла. По умолчанию будет использовано оригинальное.
		:type filename: str | None
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:param force_mode: Переключает режим перезаписи существующих изображений.
		:type force_mode: bool
		:return: Результат скачивания изображения.
		:rtype: ImageDownloadingResult
		"""

		return self.download_image(url, filename = filename, is_full_filename = is_full_filename, force_mode = force_mode)