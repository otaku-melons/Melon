from dublib.CLI.TextStyler.FastStyler import FastStyler

from typing import TYPE_CHECKING

from prettytable import PLAIN_COLUMNS, PrettyTable

if TYPE_CHECKING:
	from dublib.Engine.Bus import ExecutionStatus

def CachingSummary(result: "ExecutionStatus"):
	"""
	Выводит в консоль результат кэширования пар ID-алиас тайтлов.

	:param result: Результат кэширования.
	:type result: ExecutionStatus
	"""

	Total = result["total"]
	InCache = result["in_cache"]
	Cached = result["cached"]
	Errors: tuple[str] = result["errors"]

	print(f"Total: {Total}. Found in cache: {InCache} Cached: {Cached}.")

	if Errors:
		print(FastStyler("Errors:").decorate.bold)
		for Error in Errors: print(" - " + FastStyler(Error + ".json").colorize.red)

def OptionStatus(text: str, status: bool):
	"""
	Выводит в консоль форматированный статус опции.
		text – название опции;\n
		status – статус.
	"""

	status = FastStyler("enabled").colorize.green if status else FastStyler("disabled").colorize.red
	print(f"{text}: {status}")

def ParsersTable(columns: dict[str, list], sort_by: str = "NAME"):
	"""
	Выводит в консоль форматированную таблицу установленных парсеров.
		columns – данные для вывода;\n
		sort_by – название колонки для сортировки.
	"""

	TableObject = PrettyTable()
	TableObject.set_style(PLAIN_COLUMNS)
	Implementations = ["collect"]
	ImplementationStatuses = {
		True: FastStyler("true").colorize.green,
		False: FastStyler("false").colorize.yellow,
		None: FastStyler("error").colorize.red,
	}

	for SiteIndex in range(len(columns["SITE"])):
		columns["SITE"][SiteIndex] = FastStyler(columns["SITE"][SiteIndex]).decorate.italic

	for ColumnName in Implementations:

		for StatusIndex in range(len(columns[ColumnName])):
			columns[ColumnName][StatusIndex] = ImplementationStatuses[columns[ColumnName][StatusIndex]]

	for ColumnName in columns.keys():
		Buffer = FastStyler(ColumnName).decorate.bold
		TableObject.add_column(Buffer, columns[ColumnName])

	TableObject.align = "l"
	TableObject.sortby = FastStyler(sort_by).decorate.bold
	TableObject = str(TableObject).strip()
	Link = FastStyler("https://github.com/Otaku-Melons").decorate.underlined
	print(TableObject if TableObject else f"Parsers not installed. See {Link} for more info.")

def ParsingProgress(index: int, count: int):
	"""
	Выводит прогресс обработки множества элементов.
		index – индекс обрабатываемого элемента;\n
		count – количество жлементов.
	"""

	Number = index + 1
	Progress = round(Number / count * 100, 2)
	Number = FastStyler(str(Number)).colorize.magenta
	if str(Progress).endswith(".0"): Progress = str(int(Progress))
	elif len(str(Progress).split(".")[-1]) == 1: Progress = str(Progress) + "0"
	else: Progress = str(Progress)
	Progress = FastStyler(Progress + "%").colorize.cyan
	print(f"[{Number} / {count} | {Progress}] ", end = "")

def ParsingSummary(parsed: int, not_found: int, errors: int):
	"""
	Выводит в консоль результат парсинга.
		parsed – количество успешно полученных тайтлов;\n
		not_found – количество не найденных в источнике тайтлов;\n
		errors – количество ошибок.
	"""

	print("===== SUMMARY =====")
	parsed = FastStyler(str(parsed)).colorize.green if parsed else FastStyler(str(parsed)).colorize.red
	not_found = FastStyler(str(not_found)).colorize.yellow if not_found else FastStyler(str(not_found)).colorize.green
	errors = FastStyler(str(errors)).colorize.red if errors else FastStyler(str(errors)).colorize.green
	print(f"Parsed: {parsed}. Not found: {not_found}. Errors: {errors}.")