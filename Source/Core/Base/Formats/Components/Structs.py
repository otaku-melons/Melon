import enum

class By(enum.Enum):
	"""Типы идентификаторов описательных файлов."""
	
	Filename = None
	Slug = "slug"
	ID = "id"

class ContentTypes(enum.Enum):
	"""Перечисление типов контента."""

	Anime = "anime"
	Manga = "manga"
	Ranobe = "ranobe"
	Unknown = None
	
class Statuses(enum.Enum):
	"""Определения статусов."""

	announced = "announced"
	ongoing = "ongoing"
	completed = "completed"
	dropped = "dropped"