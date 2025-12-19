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
	# >>>>> СИСТЕМЫ СБОРКИ <<<<< #
	#==========================================================================================#

	def __epub3(self, title: "Ranobe", chapter: "Chapter", directory: str) -> str:
		"""Система сборки: EPUB3."""

		Book = epub.EpubBook()
		Book.set_title(title.localized_name)
		Book.set_language(title.content_language)
		for Author in title.authors: Book.add_author(Author)

		# Create chapter in English
		c1 = epub.EpubHtml(title = "Introduction", file_name="introduction.xhtml", lang="en")
		c1.content = (
			"<h1>The Book of the Mysterious</h1>"
			"<p>Welcome to a journey into the unknown. In these pages, you'll discover "
			"secrets that have remained hidden for centuries.</p>"
			'<p><img alt="Book Cover" src="static/ebooklib.gif"/></p>'
		)
		# Create chapter in German
		c2 = epub.EpubHtml(title="Einführung", file_name="einfuehrung.xhtml", lang="de")
		c2.content = (
			"<h1>Das Buch des Geheimnisvollen</h1>"
			"<p>Willkommen zu einer Reise ins Unbekannte. Auf diesen Seiten werden Sie "
			"Geheimnisse entdecken, die jahrhundertelang verborgen geblieben sind.</p>"
		)

		# Create image from the local image
		img = epub.EpubImage(
			uid="image_1",
			file_name="static/ebooklib.gif",
			media_type="image/gif",
			content=open("ebooklib.gif", "rb").read(),
		)

		# Define CSS style
		nav_css = epub.EpubItem(
			uid="style_nav",
			file_name="style/nav.css",
			media_type="text/css",
			content="BODY {color: black; background-color: white;}",
		)

		# Every chapter must me added to the book
		book.add_item(c1)
		book.add_item(c2)
		# This also includes images, style sheets, etc.
		book.add_item(img)
		book.add_item(nav_css)

		# Define Table Of Contents
		book.toc = (
			epub.Link("introduction.xhtml", "Introduction", "intro"),
			(epub.Section("Deutsche Sektion"), (c2,)),
		)

		# Basic spine
		book.spine = ["nav", c1, c2]

		# Add default NCX (not required) and Nav files.
		book.add_item(epub.EpubNcx())
		book.add_item(epub.EpubNav())

		# Write to the file
		epub.write_epub("the_book_of_the_mysterious.epub", book)

		pass

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""

		self.__BuildSystemsMethods = {
			RanobeBuildSystems.EPUB3: self.__epub3
		}

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

		ChapterContent = epub.EpubHtml(
			title = chapter.name,
			file_name = f"{chapter.id}.xhtml",
			content = "".join(chapter.paragraphs),
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
		self._SystemObjects.logger.info(f"Building branch {TargetBranch.id}...")

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