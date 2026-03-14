from typing import Iterable
import re

from bs4 import BeautifulSoup, Tag

def SplitParagraph(soup: BeautifulSoup, paragraph: Tag, splitter: str | re.Pattern | None = None) -> tuple[Tag]:
	"""
	Разбивает абзац на несколько абзацев по вхождению указанного идентификатора разрыва.

	:param soup: Парсер страницы.
	:type soup: BeautifulSoup
	:param paragraph: Разбиваемый абзац.
	:type paragraph: Tag
	:param splitter: Строка или паттерн регулярного выражения для разбиения параграфа. По умолчанию паттерн тегов разрыва `<br\\s*/?>`.
	:type splitter: str | re.Pattern | None
	:return: Последовательность абзацев. Если идентификатор разрыва не обнаружен, кортеж содержит лишь один оригинальный абзац.
	:rtype: tuple[Tag]
	:raises TypeError: Выбрасывается при передаче неверного типа паттерна.
	:raises ValueError: Выбрасывается при передаче тега отличного от параграфа.
	"""

	if paragraph.name != "p": raise ValueError("Only paragraph tags supports.")
	if not splitter: splitter = re.compile(r"<br\s*/?>")
	Text = paragraph.decode_contents()

	Parts: list[Tag] = list()

	if type(splitter) == re.Pattern:
		if not re.findall(splitter, Text): return (paragraph,)
		
		for Line in re.split(splitter, Text):
			Line = Line.strip()
			if Line: Parts.append(Line)
		 
	elif type(splitter) == str:
		if splitter not in Text: return (paragraph,)

		for Line in Text.split(splitter):
			Line = Line.strip()
			if Line: Parts.append(Line)

	else: raise TypeError("Pattern must be str or re.Pattern.")

	return tuple(soup.new_tag("p", string = Part, attrs = paragraph.attrs.copy()) for Part in Parts)

def UnwrapInnerTags(tag: Tag, unwrapable_tags: Iterable[str] = ("blockquote", "img", "h3"), recursive: bool = False) -> Tag:
	"""
	Производит поиск разворачиваемых тегов внутри обрабатываемого.

	:param tag: Обрабатываемый тег.
	:type tag: Tag
	:param unwrapable_tags: Последовательность имён разворачиваемых тегов.
	:type unwrapable_tags: Iterable[str]
	:param recursive: При активации поиск вложенных тегов будет производиться рекурсивно внутри каждого дочернего тега.
	:type recursive: bool
	:return: Первый найденный разворачиваемый тег или оригинальный тег.
	:rtype: Tag
	"""

	for InnerTagName in unwrapable_tags:
		InnerTag = tag.find(InnerTagName, recursive = recursive)
		if InnerTag: return InnerTag

	return tag