from dataclasses import dataclass

@dataclass(frozen = True)
class TemplateMatch:
	"""Результат поиска шаблона в изображении."""

	threshold: float
	start: float
	end: float