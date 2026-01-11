from Source.Core.Base.Builders.BaseBuilder import BaseBuilder

from dublib.Methods.Filesystem import ListDir, NormalizePath

from typing import TYPE_CHECKING
import shutil
import enum
import os

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.MangaParser import MangaParser
	from Source.Core.Base.Formats.Manga import Branch, Chapter, Manga

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

class MangaBuildSystems(enum.Enum):
	"""Перечисление систем сборки глав манги."""

	Simple = "simple"
	ZIP = "zip"
	CBZ = "cbz"

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class MangaBuilder(BaseBuilder):
	"""Сборщик манги."""

	#==========================================================================================#
	# >>>>> СИСТЕМЫ СБОРКИ <<<<< #
	#==========================================================================================#

	def __cbz(self, title: "Manga", chapter: "Chapter", directory: str) -> str:
		"""Система сборки: *.CBZ-архив."""

		ArchivePath = self.__zip(title, chapter, directory)
		OutputPath = ArchivePath[:-3] + "cbz"
		os.rename(ArchivePath, OutputPath)

		return OutputPath

	def __simple(self, title: "Manga", chapter: "Chapter", directory: str) -> str:
		"""Система сборки: каталог с изображениями."""

		ChapterName = self._GenerateChapterNameByTemplate(chapter)
		Volume = ""
		if self.__SortingByVolumes and chapter.volume: Volume = self._GenerateVolumeNameByTemplate(chapter)
		OutputPath = f"{self._ParserSettings.common.archives_directory}/{title.used_filename}/{Volume}/{ChapterName}"
		OutputPath = NormalizePath(OutputPath)

		if not os.path.exists(OutputPath): os.makedirs(OutputPath)
		Files = ListDir(directory)
		for File in Files: os.replace(f"{directory}/{File}", f"{OutputPath}/{File}")

		return OutputPath

	def __zip(self, title: "Manga", chapter: "Chapter", directory: str) -> str:
		"""Система сборки: *.ZIP-архив."""

		ChapterName = self._GenerateChapterNameByTemplate(chapter)
		Volume = ""
		if self.__SortingByVolumes and chapter.volume: Volume = self._GenerateVolumeNameByTemplate(chapter)
		OutputPath = f"{self._ParserSettings.common.archives_directory}/{title.used_filename}/{Volume}/{ChapterName}"
		OutputPath = NormalizePath(OutputPath)

		shutil.make_archive(OutputPath, "zip", directory)

		return OutputPath + ".zip"

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		self.__BuildSystemsMethods = {
			MangaBuildSystems.Simple: self.__simple,
			MangaBuildSystems.CBZ: self.__cbz,
			MangaBuildSystems.ZIP: self.__zip,
		}

		self.__SortingByVolumes = False

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def build_chapter(self, title: "Manga", chapter_id: int):
		"""
		Строит главу манги.
			title – данные тайтла;\n
			chapter_id – ID целевой главы;\n
			build_system – система сборки главы.
		"""

		self._SystemObjects.logger.info(f"Building chapter {chapter_id}…")

		if not self._BuildSystem: self._BuildSystem = MangaBuildSystems.Simple

		TargetChapter: "Chapter" = self._FindChapter(title.branches, chapter_id)
		SlidesCount = len(TargetChapter.slides)
		WorkDirectory = f"{self._Temper.builder_temp}/{title.used_filename}"

		for Slide in TargetChapter.slides:
			Link: str = Slide["link"]
			Filename: str = Link.split("/")[-1]
			Index: int = Slide["index"]
			
			if not os.path.exists(WorkDirectory): os.mkdir(WorkDirectory)
			Parser: "MangaParser" = title.parser
			print(f"[{Index} / {SlidesCount}] Downloading \"{Filename}\"… ", flush = True, end = "")
			DownloadingStatus = Parser.image(Link)
			DownloadingStatus.print_messages()

			if not DownloadingStatus.has_errors:
				print("Done.")
				self._SystemObjects.logger.info(f"Slide \"{Filename}\" downloaded.", stdout = False)

			else: self._Logger.error(f"Unable download slide \"{Filename}\". Response code: {DownloadingStatus.code}.")

			MovingStatus = self._Parser.images_downloader.move_from_temp(WorkDirectory, Filename, f"{Index}", is_full_filename = False)
			MovingStatus.print_messages()
			self.__BuildSystemsMethods[self._BuildSystem](title, TargetChapter, WorkDirectory)

		shutil.rmtree(WorkDirectory)

	def build_branch(self, title: "Manga", branch_id: int | None = None):
		"""
		Строит ветвь контента манги.
			branch_id – ID выбранной ветви (по умолчанию самая длинная).
		"""

		TargetBranch: "Branch" = self._SelectBranch(title.branches, branch_id)
		self._SystemObjects.logger.info(f"Building branch {TargetBranch.id}…")
		for CurrentChapter in TargetBranch.chapters: self.build_chapter(title, CurrentChapter.id)

	def select_build_system(self, build_system: str | None):
		"""
		Задаёт систему сборки контента.
			build_system – название системы сборки.
		"""

		self._BuildSystem = MangaBuildSystems(build_system) if build_system else None