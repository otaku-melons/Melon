from Source.Core.Exceptions import UnsupportedFormat

from dublib.Methods.Filesystem import ListDir, ReadJSON

def SafelyReadTitleJSON(path: str) -> dict:
	"""
	Безопасно читает файл JSON, проверяя его формат и валидность.

	:param path: Путь к JSON файлу.
	:type path: str
	:raises JSONDecodeError: Ошибка десериализации JSON.
	:raises UnsupportedFormat: Неподдерживаемый формат JSON.
	:return: Словарное представление JSON тайтла.
	:rtype: dict
	"""

	Formats: tuple[str] = tuple(File[:-3] for File in ListDir("Docs/Examples"))
	Data = ReadJSON(path)
	if "format" not in Data.keys(): raise UnsupportedFormat()
	elif Data["format"] not in Formats: raise UnsupportedFormat(Data["format"])

	return Data
