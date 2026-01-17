#==========================================================================================#
# >>>>> ФУНКЦИИ <<<<< #
#==========================================================================================#

def CheckLanguageCode(language_code: str, exception: bool = True) -> bool:
	"""
	Проверяет соответствие языкового кода стандарту ISO 639-3.

	:param language_code: Языковой код.
	:type language_code: str
	:param exception: Указывает, выбрасывать ли исключение.
	:type exception: bool
	:return: Возвращает `True`, если код соответствует стандарту.
	:rtype: bool
	:raise ValueError: Выбрасывается при несоответствии кода стандарту.
	"""

	IsCorrect = True
	
	if len(language_code) != 3:
		IsCorrect = False
		if exception: raise ValueError("Language code must contain only 3 characters.")
	
	if not language_code.isalpha():
		IsCorrect = False
		if exception: raise ValueError("Language code must contain only letters.")

	if not language_code.islower():
		IsCorrect = False
		if exception: raise ValueError("Language code must be in lowercase.")

	return IsCorrect

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class WordsDictionary:
	"""Словарь ключевых слов."""

	#==========================================================================================#
	# >>>>> ЧАСТИ НУМЕРАЦИИ ГЛАВ <<<<< #
	#==========================================================================================#

	@property
	def chapter(self) -> str | None:
		"""Глава."""

		return self._Data["chapter"]
	
	@property
	def volume(self) -> str | None:
		"""Том."""

		return self._Data["volume"]

	#==========================================================================================#
	# >>>>> ЧАСТИ ТИПИЗАЦИИ ГЛАВ <<<<< #
	#==========================================================================================#

	@property
	def afterword(self) -> str | None:
		"""Послесловие."""

		return self._Data["afterword"]
	
	@property
	def art(self) -> str | None:
		"""Иллюстрация."""

		return self._Data["art"]
	
	@property
	def epilogue(self) -> str | None:
		"""Эпилог."""

		return self._Data["epilogue"]

	@property
	def extra(self) -> str | None:
		"""Экстра."""

		return self._Data["extra"]
	
	@property
	def glossary(self) -> str | None:
		"""Глоссарий."""

		return self._Data["glossary"]
	
	@property
	def prologue(self) -> str | None:
		"""Пролог."""

		return self._Data["prologue"]

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def additional_data(self) -> dict[str, str]:
		"""Словарь дополнительных данных."""

		return self._AdditionalData

	@property
	def language_code(self) -> str | None:
		"""Код языка по стандарту ISO 639-3."""

		return self._Language

	#==========================================================================================#
	# >>>>> ЗАЩИЩЁННЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _CheckData(self):
		"""
		Проверяет валидность данных.

		:raises ValueError: Выбрасывается при ошибке валидации.
		"""

		if tuple(sorted(self._Data.keys())) != self._Keys: raise ValueError("Invalid dictionary keys.")

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _GenerateData(self):
		"""Переопределите данный метод для заполнения стандартного словаря данных."""

		for Key in self._Keys: self._Data[Key] = None

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, language_code: str | None):
		"""
		Словарь ключевых слов.

		:param language_code: Код языка словаря по стандарту ISO 639-3.
		:type language_code: str | None
		"""

		self._Language = language_code

		self._AdditionalData: dict[str, str] = dict()
		self._Keys = ("afterword", "art", "chapter", "epilogue", "extra", "glossary", "prologue", "volume")
		self._Data: dict[str, str | None] = dict()

		self._GenerateData()
		self._CheckData()
		if self._Language: CheckLanguageCode(self._Language)

	def __setitem__(self, key: str, value: str):
		"""
		Задаёт значение в словаре.

		:param key: Ключ.
		:type key: str
		:param value: Значение.
		:type value: str
		:raise KeyError: Выбрасывается при попытке определить нестандартное значение.
		"""

		if key not in self._Data: raise KeyError(f"Key \"{key}\" is non-standard. Should use additional data.")
		self._Data[key] = value

	def set_language_code(self, language_code: str):
		"""
		Задаёт код языка словаря.

		:param language_code: Код языка словаря по стандарту ISO 639-3.
		:type language_code: str
		:raise ValueError: Выбрасывается при несоответствии кода стандарту.
		"""

		CheckLanguageCode(language_code)
		self._Language = language_code