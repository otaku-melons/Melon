from dublib.Methods.Filesystem import NormalizePath
from dublib.Engine.Bus import ExecutionStatus
from dublib.WebRequestor import WebRequestor

from dataclasses import dataclass
from typing import TYPE_CHECKING
from pathlib import Path
from os import PathLike
from io import BytesIO
import shutil
import os

from PIL import Image

if TYPE_CHECKING:
	from Source.Core.SystemObjects import SystemObjects

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

@dataclass(frozen = True)
class ImageResolution:
	width: int
	height: int

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class ImagesDownloader:
	"""Оператор загрузки изображений."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def requestor(self) -> WebRequestor:
		"""Установленный менеджер запросов."""

		return self.__Requestor
			
	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#
	
	def __init__(self, system_objects: "SystemObjects", requestor: WebRequestor):
		"""
		Оператор загрузки изображений.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param requestor: Менеджер запросов.
		:type requestor: WebRequestor
		"""
		
		self.__SystemObjects = system_objects
		self.__Requestor = requestor

		self.__ParserSettings = self.__SystemObjects.manager.current_parser_settings

	def get_image_resolution(self, data: bytes) -> ImageResolution | None:
		"""
		Получает разрешение иллюстрации. Вычисляется на основе бинарного представления.

		При отключении опцией парсера возвращает `None`.

		:return: Разрешение изображения или `None` при ошибке вычисления или отключении получения размера.
		:rtype: ImageResolution | None
		"""

		if not self.__ParserSettings.common.sizing_images: return
		if not data: return

		Resolution = None

		try:
			Buffer = Image.open(BytesIO(data))
			Resolution = ImageResolution(Buffer.size[0], Buffer.size[1])

		except: return

		return Resolution

	def is_exists(self, url: str, directory: PathLike | None = None, filename: str | None = None, is_full_filename: bool = True) -> bool:
		"""
		Проверяет существование изображения в целевой директории по ссылке.

		:param url: Ссылка на изображение.
		:type url: str
		:param directory: Целевая директория. По умолчанию будет проверен временный каталог парсера.
		:type directory: PathLike | None
		:param filename: Имя файла. По умолчанию будет сгенерировано на основе URL.
		:type filename: str | none
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:return: Возвращает `True`, если файл с таким именем уже существует в директории.
		:rtype: bool
		"""

		ParsedURL = Path(url)
		Filetype = ""
		if not is_full_filename: Filetype = ParsedURL.suffix
		if not filename: filename = ParsedURL.stem

		if not directory: directory = self.__SystemObjects.temper.parser_temp
		else: directory = NormalizePath(directory)

		return os.path.exists(f"{directory}/{filename}{Filetype}")

	def image(self, url: str, directory: PathLike | None = None, filename: str | None = None, is_full_filename: bool = False) -> ExecutionStatus:
		"""
		Скачивает изображение.

		:param url: Ссылка на изображение.
		:type url: str
		:param directory: Путь к каталогу, в который нужно сохранить файл. По умолчанию будет использован временный каталог парсера.
		:type directory: PathLike | None
		:param filename: Имя файла. По умолчанию будет сгенерировано на основе URL.
		:type filename: str | None
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:return: Контейнер статуса выполнения. Содержит следующие поля данных: `exists` – указывает, существовал ли файл в каталоге загрузки на момент вызова метода; `replaced_by_stup` – указывает, заменено ли изображение заглушкой.
		:rtype: ExecutionStatus
		"""

		Status = ExecutionStatus()
		Status["exists"] = False
		Status["replaced_by_stup"] = False
		Status["resolution"] = None
		if not directory: directory = self.__SystemObjects.temper.parser_temp
		else: directory = NormalizePath(directory)

		#---> Определение параметров файла.
		#==========================================================================================#
		ParsedURL = Path(url)
		Filetype = ""
		if not is_full_filename: Filetype = ParsedURL.suffix
		if not filename: filename = ParsedURL.stem
		ImagePath = f"{directory}/{filename}{Filetype}"

		if os.path.exists(ImagePath):
			Status["exists"] = True
			Status.value = filename + Filetype

		#---> Скачивание файла.
		#==========================================================================================#
		if not Status["exists"] or self.__SystemObjects.FORCE_MODE:
			Response = self.__Requestor.get(url)
			Status.code = Response.status_code
			IsDownloaded = False

			if Response.status_code == 200:
				Status["resolution"] = self.get_image_resolution(Response.content)
				
				if len(Response.content) > 1000:
					with open(ImagePath, "wb") as FileWriter: FileWriter.write(Response.content)
					Status.value = filename + Filetype
					IsDownloaded = True

					if Status["exists"]: Status.push_message("Overwritten.")
					else: Status.push_message("Done.")
					
				elif self.__ParserSettings.common.bad_image_stub: Message = f"Image doesn't contain enough bytes: \"{url}\"."

			elif Response.status_code == 404: Message = f"Image not found: \"{url}\"."
			else: Message = f"Unable to download image: \"{url}\"."

			#---> Замена изображения заглушкой.
			#==========================================================================================#
			if not IsDownloaded and self.__ParserSettings.common.bad_image_stub:
				shutil.copy2(self.__ParserSettings.common.bad_image_stub, ImagePath)
				Message = f"{Message} Replaced by stub."
				Status["replaced_by_stup"] = True
				Status.push_warning(Message)

			elif not IsDownloaded:
				Status.push_error(Message)
				if not Response.ok: self.__SystemObjects.logger.request_error(Response, Message, exception = False)
				else: self.__SystemObjects.logger.error(Message)

		else: Status.push_message("Already exists.")
			
		return Status

	def move_from_temp(self, directory: PathLike, original_filename: str, filename: str | None = None, is_full_filename: bool = True) -> ExecutionStatus:
		"""
		Перемещает изображение из временного каталога парсера в друкгую директорию.

		:param directory: Целевая директория.
		:type directory: PathLike
		:param original_filename: Имя файла во временном каталоге пользователя.
		:type original_filename: str
		:param filename: Новое имя файла. По умолчанию будет использовано оригинальное.
		:type filename: str | None
		:param is_full_filename: Указывает, является ли новое имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе оригинального имени), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:return: Контейнер статуса выполнения. Под ключём `exists` содержится информация о том, существовал ли файл в целевом каталоге на момент вызова метода.
		:rtype: ExecutionStatus
		"""
		
		Status = ExecutionStatus()
		Status["exists"] = False
		Filetype = ""

		if filename and not is_full_filename:
			Filetype = Path(original_filename).suffix
			filename = Path(filename).stem
			
		elif not filename: filename = original_filename

		directory = NormalizePath(directory)
		OriginalPath = f"Temp/{self.__SystemObjects.parser_name}/{original_filename}"
		TargetPath = f"{directory}/{filename}{Filetype}"

		if os.path.exists(TargetPath): 
			Status.value = True
			Status["exists"] = True

		else:
			shutil.move(OriginalPath, TargetPath)
			Status.value = True

		return Status
	
	def temp_image(self, url: str, filename: str | None = None, is_full_filename: bool = False) -> ExecutionStatus:
		"""
		Скачивает изображение во временный каталог парсера..

		:param url: Ссылка на изображение.
		:type url: str
		:param filename: Имя файла. По умолчанию будет использовано оригинальное.
		:type filename: str | None
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:return: Контейнер статуса выполнения.
		:rtype: ExecutionStatus
		"""

		return self.image(url, filename = filename, is_full_filename = is_full_filename)