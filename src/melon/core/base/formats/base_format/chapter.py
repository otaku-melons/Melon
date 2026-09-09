from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Sequence, cast

from dublib.functions.data import zerotify
from dublib.functions.data.dictionary import insert_dictionary_after_key
from dublib.functions.data.string import remove_recurring_substrings

if TYPE_CHECKING:
	from ...parsers.base_parser import BaseParser

class ExtraData:
	"""Дополнительные данные главы."""

	def __init__(self, base_keys: Sequence[str]):
		"""
		Дополнительные данные главы.

		:param base_keys: Последовательность базовых ключей, которые не могут быть использованы в дополнительных данных.
		:type base_keys: Sequence[str]
		"""

		self.__BaseKeys = base_keys

		self.__data: dict = {}

	def clear(self):
		"""Удаляет все дополнительные данные."""

		self.__data.clear()

	def exists(self, key: str) -> bool:
		"""
		Проверяет существования дополнительных данных.

		:param key: Проверяемый ключ.
		:type key: str
		:return: Возвращает `True`, если ключ найден.
		:rtype: bool
		:raises ValueError: Ключ зарезервирован обязательными значениями.
		"""

		if key in self.__BaseKeys:
			raise ValueError("Key ir reserved by important values, not extra.")

		return key in self.__data

	def from_dict(self, data: dict):
		"""
		Копирует все пары ключ-значение, ключи которых не являются обязательными, в дополнительные данные.

		:param data: Словарь данных главы.
		:type data: dict
		"""

		for Key in data.keys():
			if Key not in self.__BaseKeys:
				self.set(Key, data[Key])

	def get(self, key: str) -> Any:
		"""
		Возвращает дополнительные данные главы.
		
		:param key: Ключ, под которым хранятся дополнительные данные.
		:type key: str
		:return: Дополнительные данные.
		:rtype: Any
		:raises KeyError: Ключ не найден.
		"""

		return self.__data[key]

	def remove(self, key: str):
		"""
		Удаляет дополнительные данные главы. Игнорирует отсутствие ключа.
		
		:param key: Ключ, под которым хранятся дополнительные данные.
		:type key: str
		"""

		if key in self.__data:
			del self.__data[key]

	def set(self, key: str, value: Any):
		"""
		Задаёт дополнительные данные.

		:param key: Ключ.
		:type key: str
		:param value: Значение.
		:type value: Any
		:raises KeyError: Ключ используется для обязательных полей данных.
		"""

		if key in self.__BaseKeys:
			raise KeyError(key)
	
		self.__data[key] = value

	def to_dict(self) -> dict:
		"""
		Возвращает словарное представление объекта.

		:return: Словарное представление объекта.
		:rtype: dict
		"""
	
		return self.__data.copy()

class BaseChapter(ABC):
	"""Базовая глава."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def id(self) -> int:
		"""Уникальный идентификатор главы."""

		return self._data["id"]
	
	@property
	def slug(self) -> str | None:
		"""Алиас главы."""

		return self._data["slug"]

	@property
	def volume(self) -> str | None:
		"""Номер тома."""

		return self._data["volume"]
	
	@property
	def number(self) -> str | None:
		"""Номер главы."""

		return self._data["number"]
	
	@property
	def name(self) -> str | None:
		"""Название главы."""

		return self._data["name"]

	@property
	def is_empty(self) -> bool:
		"""Состояние: пуста ли глава."""

		return self._is_empty()

	@property
	def is_paid(self) -> bool | None:
		"""Состояние: платная ли глава."""

		return self._data["is_paid"]
	
	@property
	def workers(self) -> tuple[str]:
		"""Набор идентификаторов лиц, адаптировавших контент."""

		return tuple(self._data["workers"])
	
	@property
	def extra_data(self) -> ExtraData:
		"""Дополнительные данные главы."""

		return self._extra_data

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PrettyNumber(self, number: float | int | str | None) -> str | None:
		"""
		Преобразует номер главы или тома в корректное значение.

		:param number: Номер главы или тома.
		:type number: float | int | str | None
		:return: Откорректированный номер.
		:rtype: str | None
		"""

		if number is None: number = ""
		elif type(number) is not str: number = str(number)
		if "-" in number: number = number.split("-")[0]
		number = number.strip("\t .\n")
		Number = cast("str | None", zerotify(number))

		return Number

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	@abstractmethod
	def _clear(self):
		"""Очищает контент главы."""

		pass

	@abstractmethod
	def _from_dict(self, data: dict):
		"""
		Заполняет данные главы из словаря.

		:param data: Словарь данных главы.
		:type data: dict
		"""

		pass

	@abstractmethod
	def _is_empty(self) -> bool:
		"""
		Проверяет, пустая ли глава.

		:return: Состояние: пуста ли глава.
		:rtype: bool
		"""

		return False

	def _post_init(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass

	def _pre_formatter(self):
		"""Метод, запускающийся перед генерацией словарного представления объекта."""

		pass

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, parser: "BaseParser", chapter_id: int):
		"""
		Базовая глава.

		:param parser: Парсер.
		:type parser: BaseParser
		:param chapter_id: ID главы.
		:type chapter_id: int
		"""

		self._parser = parser

		self._data: dict[str, Any] = {
			"id": chapter_id,
			"slug": None,
			"volume": None,
			"number": None,
			"name": None,
			"is_paid": None,
			"workers": []
		}

		self._post_init()
		self._extra_data = ExtraData(tuple(self._data.keys()))

	def add_worker(self, worker: str):
		"""
		Добавляет идентификатор лица, адаптировавшего контент.

		:param worker: Идентификатор.
		:type worker: str
		"""

		if worker not in self._data["workers"]:
			self._data["workers"].append(worker)

	def clear(self):
		"""Удаляет содержимое главы."""

		self._clear()

	def from_dict(self, data: dict):
		"""
		Заполняет данные главы из словаря.

		:param data: Словарь данных главы.
		:type data: dict
		"""

		self._from_dict(data)
		self.extra_data.from_dict(data)

	def set_is_paid(self, is_paid: bool | None):
		"""
		Указывает, является ли глава платной.

		:param is_paid: Состояние: платная ли глава.
		:type is_paid: bool | None
		"""

		self._data["is_paid"] = is_paid

	def set_name(self, name: str | None):
		"""
		Задаёт название главы.

		:param name: Название главы.
		:type name: str | None
		"""

		name = zerotify(name)
		if name: name = name.strip()
		
		if name and self._parser.settings.common.pretty:
			if name.endswith("..."): name = name.rstrip(".") + "…"
			else: name = name.rstrip(".–")
		
			name = name.replace("\u00A0", " ")
			name = remove_recurring_substrings(name, " ")

			name = name.rstrip(":.")

		self._data["name"] = name

	def set_number(self, number: float | int | str | None):
		"""
		Задаёт номер главы.

		:param number: Номер главы.
		:type number: float | int | str | None
		"""
		
		self._data["number"] = self._PrettyNumber(number)

	def set_workers(self, workers: Sequence[str]):
		"""
		Задаёт идентификаторы лиц, адаптировавших контент.

		:param workers: Набор идентификаторов.
		:type workers: Sequence[str]
		"""

		for Worker in workers:
			self.add_worker(Worker)

	def set_slug(self, slug: str | None):
		"""
		Задаёт алиас главы.

		:param slug: Алиас главы.
		:type slug: str | None
		"""

		self._data["slug"] = slug

	def set_volume(self, volume: float | int | str | None):
		"""
		Задаёт номер тома, к которому принадлежит глава.

		:param volume: Номер тома.
		:type volume: float | int | str | None
		"""

		self._data["volume"] = self._PrettyNumber(volume)

	def to_dict(self) -> dict:
		"""Возвращает копию словаря данных главы."""

		self._pre_formatter()

		return insert_dictionary_after_key(self._data.copy(), self.extra_data.to_dict(), "workers")
