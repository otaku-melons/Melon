from Source.Core.Base.Builders.BaseBuilder import BaseBuilder

from dataclasses import dataclass
from typing import TYPE_CHECKING
import enum

from ebooklib import epub

if TYPE_CHECKING:
	from Source.Core.Base.Parsers.RanobeParser import RanobeParser
	from Source.Core.Base.Formats.Ranobe import Branch, Chapter, Ranobe

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

@dataclass
class ChapterItems:
	content: epub.EpubHtml
	images: tuple[epub.EpubImage] = tuple()

class RanobeBuildSystems(enum.Enum):
	"""Перечисление систем сборки ранобэ."""

	EPUB3 = "epub3"

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class RanobeBuilder(BaseBuilder):
	"""Сборщик ранобэ."""

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def build_chapter(self, title: "Ranobe", chapter: "Chapter") -> ChapterItems:
		"""
		Строит главу ранобэ.

		:param title: Данные тайтла.
		:type title: Ranobe
		:param chapter: Данные главы.
		:type chapter: Chapter
		:return: Набор элементов EPUB3.
		:rtype: ChapterItems
		"""

		ChapterTitle = ""
		ChapterNumeration = ""
		if chapter.volume: ChapterNumeration = f"Том {chapter.volume}. "
		if chapter.number: ChapterNumeration += f"Глава {chapter.number}. "
		if chapter.name: ChapterTitle = ChapterNumeration + chapter.name

		ChapterContent = epub.EpubHtml(
			title = ChapterTitle,
			file_name = f"{chapter.id}.xhtml",
			content = f"<h2>{ChapterNumeration}{chapter.name}</h2>" + "".join(chapter.paragraphs),
			lang = title.content_language
		)
		
		return ChapterItems(ChapterContent)

	def build_branch(self, title: "Ranobe", branch_id: int | None = None):
		"""
		Собирает ветвь контента ранобэ.

		:param title: Данные тайтла.
		:type title: Ranobe
		:param branch_id: ID ветви. По умолчанию собирается первая ветвь.
		:type branch_id: int | None
		"""

		TargetBranch: "Branch" = self._SelectBranch(title.branches, branch_id)
		self._SystemObjects.logger.info(f"Building branch {TargetBranch.id}…")

		Book = epub.EpubBook()
		Book.set_title(title.localized_name)
		Book.set_language(title.content_language)
		for Author in title.authors: Book.add_author(Author)
		Chapters = list()

		for CurrentChapter in TargetBranch.chapters:
			ChapterItems = self.build_chapter(title, CurrentChapter)
			Chapters.append(ChapterItems.content)
			Book.add_item(ChapterItems.content)
			for Image in ChapterItems.images: Book.add_item(Image)

		Book.toc = tuple(Chapters)
		Book.spine = ["nav"] + Chapters
		Book.add_item(epub.EpubNav())

		Directory = self._SystemObjects.manager.current_parser_settings.directories.archives
		epub.write_epub(f"{Directory}/{title.localized_name}.epub", Book)

	def select_build_system(self, build_system: str | None):
		"""
		Выбирает систему сборки.

		:param build_system: Название системы сборки. Нечувствительно к регистру.
		:type build_system: str | None
		"""

		self._BuildSystem = RanobeBuildSystems(build_system) if build_system else None