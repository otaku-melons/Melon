from Source.Core.Exceptions import ParsingError, TitleNotFound
from Source.CLI import Templates

from dublib.CLI.Templates.Bus import MessagesTypes, PrintMessage
from dublib.CLI.TextStyler import GetStyledTextFromHTML
from dublib.Methods.Filesystem import ReadJSON
from dublib.WebRequestor import WebResponse

from typing import TYPE_CHECKING
from datetime import datetime
import logging
import enum
import sys
import os
import re

import telebot

if TYPE_CHECKING:
	from Source.Core.Base.Formats.BaseFormat import BaseChapter, BaseTitle
	from Source.Core.SystemObjects import SystemObjects

#==========================================================================================#
# >>>>> ПЕРЕЧИСЛЕНИЯ <<<<< #
#==========================================================================================#

class LoggerRules(enum.Enum):
	"""Правила очистки логов."""

	Save = 0
	SaveIfHasErrors = 1
	SaveIfHasWarnings = 2
	Remove = 3

#==========================================================================================#
# >>>>> КОНТЕЙНЕРЫ НАСТРОЕК <<<<< #
#==========================================================================================#

class CleanerSettings:
	"""Правила очистки логов."""

	def __init__(self, data: dict):
		"""
		Правила очистки логов.

		:param data: Словарь правил очистки логов.
		:type data: dict
		"""

		self.__Rules = data.copy()

	def __getitem__(self, command: str) -> LoggerRules:
		"""
		Возвращает правило очистки логов.

		:param command: Имя команды.
		:type command: str
		:return: Правило очистки логов.
		:rtype: LoggerRules
		"""

		Rule = LoggerRules(0)
		if command in self.__Rules.keys(): Rule = LoggerRules(self.__Rules[command])

		return Rule

class ReportsRules:
	"""Набор правил отправки отчётов."""

	#==========================================================================================#
	# >>>>> НАСТРОЙКИ ОТПРАВКИ <<<<< #
	#==========================================================================================#

	@property 
	def attach_log(self) -> bool:
		"""Переключатель: требуется ли прикреплять файл лога к отчёту."""

		return self.__Data["attach_log"]
	
	@property 
	def forbidden_commands(self) -> list[str]:
		"""Список команд, для которых запрещена отправка отчётов."""

		return self.__Data["forbidden_commands"]
	
	#==========================================================================================#
	# >>>>> ПЕРЕКЛЮЧАТЕЛИ ОТПРАВКИ ШАБЛОНОВ <<<<< #
	#==========================================================================================#
	
	@property 
	def ignored_requests_errors(self) -> list[int, None]:
		"""Список кодов HTTP, не вызывающих отправку отчётов."""

		return self.__Data["ignored_requests_errors"]
	
	@property 
	def title_not_found(self) -> bool:
		"""Указывает, нужно ли отправлять отчёт для данного типа записи."""

		return self.__Data["title_not_found"]
	
	@property 
	def chapter_not_found(self) -> bool:
		"""Указывает, нужно ли отправлять отчёт для данного типа записи."""

		return self.__Data["chapter_not_found"]
	
	@property 
	def downloading_error(self) -> bool:
		"""Указывает, нужно ли отправлять отчёт для данного типа записи."""

		return self.__Data["downloading_error"]
	
	#==========================================================================================#
	# >>>>> ПЕРЕКЛЮЧАТЕЛИ ОТПРАВКИ СООБЩЕНИЙ ОБ ОШИБКАХ И ПРЕДУПРЕЖДЕНИЙ <<<<< #
	#==========================================================================================#

	@property 
	def critical(self) -> bool:
		"""Указывает, нужно ли отправлять отчёт для данного типа записи."""

		return self.__Data["critical"]
	
	@property 
	def errors(self) -> bool:
		"""Указывает, нужно ли отправлять отчёт для данного типа записи."""

		return self.__Data["errors"]
	
	@property 
	def warnings(self) -> bool:
		"""Указывает, нужно ли отправлять отчёт для данного типа записи."""

		return self.__Data["warnings"]
	
	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, data: dict):
		"""

		:param data: Словарь правил.
		:type data: dict
		"""

		self.__Data = data.copy()
		
		Default = {
			"attach_log": True,

			"forbidden_commands": [],
			"ignored_requests_errors": [],

			"title_not_found": True,
			"chapter_not_found": True,
			"downloading_error": True,

			"critical": True,
			"errors": True,
			"warnings": True
		}

		for Rule in Default.keys():
			if Rule not in self.__Data.keys(): self.__Data[Rule] = Default[Rule]

class TelebotSettings:
	"""Настройки бота Telegram."""

	@property 
	def enable(self) -> bool:
		"""Состояние: включена ли отправка отчётов в Telegram."""

		return self.__Data["enable"]
	
	@property 
	def bot_token(self) -> str | None:
		"""Токен бота Telegram."""

		return self.__Data["bot_token"]
	
	@property 
	def chat_id(self) -> int | None:
		"""Идентификатор чата Telegram."""

		return self.__Data["chat_id"]
	
	@property 
	def comment(self) -> str | None:
		"""Комментарий для отчёта."""

		return self.__Data["comment"]
	
	@property 
	def rules(self) -> ReportsRules:
		"""Набор правил отправки отчётов."""

		return self.__Rules
	
	def __init__(self, data: dict | None = None):
		"""
		Настройки бота Telegram

		:param data: Словарь настроек или `None` при отсутствии оных.
		:type data: dict | None
		"""

		self.__Data = data or {
			"enable": False,
			"bot_token": None,
			"chat_id": None,
			"comment": None,
			"rules": {}
		}

		self.__Rules = ReportsRules(self.__Data["rules"])

class LoggerSettings:
	"""Настройки логов."""

	@property 
	def cleaner(self) -> CleanerSettings:
		"""Правила очистки логов."""

		return self.__Cleaner
	
	@property 
	def telebot(self) -> TelebotSettings:
		"""Настройки бота Telegram."""

		return self.__Telebot

	def __init__(self, data: dict | None = None):
		"""
		Настройки логов.

		:param data: Словарь со всеми настройками логов или `None` при отсутствии.
		:type data: dict | None
		"""

		self.__Data = data or {
			"telebot": {},
			"cleaner": {}
		}

		for Key in ["telebot", "cleaner"]:
			if Key not in self.__Data.keys(): self.__Data[Key] = dict()

		self.__Telebot = TelebotSettings(self.__Data["telebot"])
		self.__Cleaner = CleanerSettings(self.__Data["cleaner"])

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Portals:
	"""Коллекция порталов CLI/логов для парсеров."""

	def __init__(self, logger: "Logger"):
		"""
		Коллекция порталов CLI/логов для парсеров.

		:param logger: Оператор вывода и логов.
		:type logger: Logger
		"""

		self.__Logger = logger

	#==========================================================================================#
	# >>>>> БАЗОВЫЕ ТИПЫ ПОРТАЛОВ <<<<< #
	#==========================================================================================#

	def critical(self, text: str):
		"""
		Портал критической ошибки.

		:param text: Текст сообщения.
		:type text: str
		"""

		self.__Logger.critical(text, stdout = True)

	def error(self, text: str):
		"""
		Портал ошибки.

		:param text: Текст сообщения.
		:type text: str
		"""

		self.__Logger.error(text, stdout = True)

	def info(self, text: str):
		"""
		Портал информационнного сообщения.

		:param text: Текст сообщения.
		:type text: str
		"""

		self.__Logger.info(text, stdout = True)

	def warning(self, text: str):
		"""
		Портал предупреждения.

		:param text: Текст сообщения.
		:type text: str
		"""

		self.__Logger.warning(text, stdout = True)

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ ПОРТАЛОВ ОШИБОК <<<<< #
	#==========================================================================================#

	def chapter_not_found(self, title: "BaseTitle", chapter: "BaseChapter"):
		"""
		Портал ошибки: глава не найдена.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param chapter: Данные главы.
		:type chapter: BaseChapter
		"""

		self.__Logger.chapter_not_found(title, chapter)

	def request_error(self, response: WebResponse, text: str | None = None, exception: bool = True):
		"""
		Портал ошибки: неудачный запрос.

		:param response: Контейнер ответа.
		:type response: WebResponse
		:param text: Описание ошибки.
		:type text: str | None
		:param exception: Указывает, выбрасывать ли исключение.
		:type exception: bool
		:raises ParsingError: Выбрасывается при активации соответствующего аргумента.
		"""

		self.__Logger.request_error(response, text, exception)

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ ПОРТАЛОВ ПРЕДУПРЕЖДЕНИЙ <<<<< #
	#==========================================================================================#

	def title_not_found(self, title: "BaseTitle", exception: bool = True):
		"""
		Портал предупреждения: тайтл не найден.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param exception: Указывает, выбрасывать ли исключение.
		:type exception: bool
		"""

		self.__Logger.title_not_found(title, exception)

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ ПОРТАЛОВ <<<<< #
	#==========================================================================================#

	def chapter_skipped(self, title: "BaseTitle", chapter: "BaseChapter", comment: str | None = None):
		"""
		Портал сообщения: дополнение главы пропущено.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param chapter: Данные главы.
		:type chapter: BaseChapter
		:param comment: Комментарий о причине пропуска.
		:type comment: str | None
		"""

		ChapterType = "Paid chapter" if chapter.is_paid else "Chapter"
		ChapterID = chapter.id if chapter.id else chapter.slug
		if ChapterID: ChapterID = " " + str(ChapterID)
		else: ChapterID = ""
		comment = f" {comment}" if comment else ""

		self.__Logger.info(f"Title: \"{title.slug}\" (ID: {title.id}). {ChapterType}{ChapterID} skipped.{comment}", stdout = False)
		PrintMessage(f"{ChapterType}{ChapterID} skipped.{comment}")

	def collect_progress_by_page(self, page: int):
		"""
		Портал сообщения: индикация прогресса сбора коллекции.

		:param page: Номер страницы каталога, с которого собраны данные.
		:type page: int
		"""

		self.__Logger.info(f"Titles on page {page} collected.")

	def covers_unstubbed(self, title: "BaseTitle"):
		"""
		Портал сообщения: обложки отфильтрованы, так как являются заглушками.

		:param title: Данные тайтла.
		:type title: BaseTitle
		"""

		self.__Logger.info(f"Title: \"{title.slug}\" (ID: {title.id}). Stubs detected. Covers downloading will be skipped.", stdout = False)
		PrintMessage("Stubs detected. Covers downloading will be skipped.")

class Logger:
	"""Оператор вывода и логов."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def portals(self) -> Portals:
		"""Набор шаблонов ввода-вывода."""

		return self.__Portals

	@property
	def templates(self) -> Templates:
		"""Набор шаблонов ввода-вывода."""

		return Templates

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __ReadSettings(self) -> LoggerSettings:
		"""
		Считвает настройки логов для конкретного парсера.

		:return: Настройки логов.
		:rtype: LoggerSettings
		"""

		LoggerSettingsObject = LoggerSettings()

		if self.__ParserName:
			Path = f"Configs/{self.__ParserName}/logger.json"
			if os.path.exists(Path): LoggerSettingsObject = LoggerSettings(ReadJSON(Path))

		return LoggerSettingsObject

	def __ReplaceTags(self, text: str) -> str:
		"""
		Заменяет теги HTML на двойные кавычки.

		:param text: Обрабатываемый текст.
		:type text: str
		:return: Обработанный текст.
		:rtype: str
		"""

		return re.sub(r"<[^>]+>", "\"", text)

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ ВЫВОДА <<<<< #
	#==========================================================================================#

	def __LogMessage(self, text: str, message_type: MessagesTypes | None = None):
		"""
		Записывает сообщение в логи.

		:param text: Текст сообщения.
		:type text: str
		:param message_type: Тип сообщения.
		:type message_type: MessagesTypes | None
		"""

		text = self.__ReplaceTags(text)

		match message_type:

			case MessagesTypes.Critical: 
				self.__IsLogHasError = True
				if not self.__SilentMode and self.__LoggerSettings.telebot.rules.critical: self.__SendReport(text)
				logging.critical(text)

			case MessagesTypes.Error: 
				self.__IsLogHasError = True
				if not self.__SilentMode and self.__LoggerSettings.telebot.rules.errors: self.__SendReport(text)
				logging.error(text)

			case MessagesTypes.Warning: 
				self.__IsLogHasWarning = True
				if not self.__SilentMode and self.__LoggerSettings.telebot.rules.warnings: self.__SendReport(text)
				logging.warning(text)

			case MessagesTypes.Info | None:
				logging.info(text)

	def __PrintMessage(self, text: str, message_type: MessagesTypes | None = None):
		"""
		Отправляет стилизованное сообщение в поток вывода.

		:param text: Текст сообщения.
		:type text: str
		:param message_type: Тип сообщения.
		:type message_type: MessagesTypes | None
		"""

		text = GetStyledTextFromHTML(text)
		PrintMessage(text, message_type)

	def __SendReport(self, description: str):
		"""
		Отправляет отчёт об ошибке в чат Telegram.

		:param description: Описание ошибки.
		:type description: str
		"""

		if self.__LoggerSettings.telebot.enable and self.__PointName not in self.__LoggerSettings.telebot.rules.forbidden_commands:
			Token = self.__LoggerSettings.telebot.bot_token
			Bot = telebot.TeleBot(Token)
			LaunchArguments = list(sys.argv)
			LaunchArguments.pop(0)
			Command = " ".join(LaunchArguments)

			Message = list()
			Message.append(f"<b>Parser:</b> {self.__ParserName}")
			if self.__LoggerSettings.telebot.comment: Message.append(f"<b>Comment:</b> {self.__LoggerSettings.telebot.comment}")
			Message.append(f"<b>Command:</b> <pre>{Command}</pre>\n\n<i>{description}</i>")
			Message = "\n".join(Message)

			if Message != self.__ErrorCache:
				self.__ErrorCache = Message
				
				try:
					if self.__LoggerSettings.telebot.rules.attach_log:
						Bot.send_document(
							self.__LoggerSettings.telebot.chat_id,
							document = open(self.__LogFilename, "rb"), 
							caption = Message,
							parse_mode = "HTML"
						)

					else:
						Bot.send_message(
							chat_id = self.__LoggerSettings.telebot.chat_id,
							text = Message,
							parse_mode = "HTML"
						)

				except Exception as ExceptionData: self.error(f"TeleBot error occurs during sending report: \"{ExceptionData}\".")

		self.__SilentMode = False

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Оператор вывода и логов.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		"""
		
		self.__SystemObjects = system_objects

		self.__Portals = Portals(self)
		self.__LoggerSettings = LoggerSettings()

		self.__LogFilename = None
		self.__ParserName = None
		self.__PointName = None
		self.__ErrorCache = None
		self.__SilentMode = False
		self.__LoggerRule = LoggerRules.SaveIfHasWarnings
		self.__IsLogHasError = False
		self.__IsLogHasWarning = False

		#---> Настройка логов.
		#==========================================================================================#
		if not os.path.exists("Logs"): os.makedirs("Logs")
		CurrentDate = datetime.now()
		self.__LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
		self.__LogFilename = self.__LogFilename.replace(":", "-")
		logging.basicConfig(filename = self.__LogFilename, encoding = "utf-8", level = logging.INFO, format = "%(asctime)s %(levelname)s: %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")

	def select_cli_point(self, point_name: str):
		"""
		Задаёт название точки CLI. Используется для обработки правил логов.

		:param point_name: Название точки CLI.
		:type point_name: str
		"""

		self.__PointName = point_name

	def select_parser(self, parser_name: str):
		"""
		Задаёт парсер, для которого будут применены настройки логгирования.

		:param parser_name: Имя парсера.
		:type parser_name: str
		"""

		self.__ParserName = parser_name
		self.__LoggerSettings = self.__ReadSettings()

	def set_rule(self, rule: int | LoggerRules):
		"""
		Задаёт правило обработки логов.

		:param rule: Индекс правила или само правило.
		:type rule: int | LoggerRules
		"""

		if type(rule) == int: self.__LoggerRule = LoggerRules(rule)
		else: self.__LoggerRule = rule

	#==========================================================================================#
	# >>>>> БАЗОВЫЕ МЕТОДЫ ВЫВОДА <<<<< #
	#==========================================================================================#

	def critical(self, text: str, stdout: bool = True, log: bool = True):
		"""
		Обрабатывает вывод критической ошибки.

		:param text: Текст сообщения.
		:type text: str
		:param stdout: Указывает, нужно ли отправлять данные в поток вывода.
		:type stdout: bool
		:param log: Указывает, нужно ли делать запись в логи.
		:type log: bool
		"""

		if stdout: self.__PrintMessage(text, MessagesTypes.Critical)
		if log: self.__LogMessage(text, MessagesTypes.Critical)

	def error(self, text: str, stdout: bool = True, log: bool = True):
		"""
		Обрабатывает вывод ошибки.

		:param text: Текст сообщения.
		:type text: str
		:param stdout: Указывает, нужно ли отправлять данные в поток вывода.
		:type stdout: bool
		:param log: Указывает, нужно ли делать запись в логи.
		:type log: bool
		"""

		if stdout: self.__PrintMessage(text, MessagesTypes.Error)
		if log: self.__LogMessage(text, MessagesTypes.Error)

	def warning(self, text: str, stdout: bool = True, log: bool = True):
		"""
		Обрабатывает вывод предупреждения.

		:param text: Текст сообщения.
		:type text: str
		:param stdout: Указывает, нужно ли отправлять данные в поток вывода.
		:type stdout: bool
		:param log: Указывает, нужно ли делать запись в логи.
		:type log: bool
		"""

		if stdout: self.__PrintMessage(text, MessagesTypes.Warning)
		if log: self.__LogMessage(text, MessagesTypes.Warning)

	def info(self, text: str, stdout: bool = True, log: bool = True):
		"""
		Обрабатывает вывод сообщения.

		:param text: Текст сообщения.
		:type text: str
		:param stdout: Указывает, нужно ли отправлять данные в поток вывода.
		:type stdout: bool
		:param log: Указывает, нужно ли делать запись в логи.
		:type log: bool
		"""

		if stdout: self.__PrintMessage(text, None)
		if log: self.__LogMessage(text, MessagesTypes.Info)

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ ОШИБОК <<<<< #
	#==========================================================================================#

	def chapter_not_found(self, title: "BaseTitle", chapter: "BaseChapter"):
		"""
		Шаблон ошибки: глава не найдена.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param chapter: Данные главы.
		:type chapter: BaseChapter
		"""

		self.__LogMessage(f"Title: \"{title.slug}\" (ID: {title.id}). Chapter {chapter.id} not found.", MessagesTypes.Error)
		self.__PrintMessage(f"Chapter {chapter.id} not found.")

	def request_error(self, response: WebResponse, text: str | None = None, exception: bool = True):
		"""
		Шаблон ошибки: неудачный запрос.

		:param response: Контейнер ответа.
		:type response: WebResponse
		:param text: Описание ошибки.
		:type text: str | None
		:param exception: Указывает, следует ли выбросить исключение.
		:type exception: bool
		:raises ParsingError: Выбрасывается при активации соответствующего аргумента.
		"""

		if not text: text = "Request error."
		Text = f"{text} Response code: {response.status_code}."

		if response.status_code not in self.__LoggerSettings.telebot.rules.ignored_requests_errors:
			self.__SendReport(Text)
			self.__SilentMode = True

		self.__LogMessage(Text, MessagesTypes.Error)
		self.__PrintMessage(Text, MessagesTypes.Error)
		self.__SilentMode = False
		if exception: raise ParsingError()

	def unsupported_format(self, title: "BaseTitle", exception: bool = False):
		"""
		Шаблон предупреждения: неподдерживаемый формат JSON.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param exception: Указывает, следует ли выбросить исключение.
		:type exception: bool
		:raises ParsingError: Выбрасывается при активации соответствующего аргумента.
		"""

		Text = "Unsupported JSON format."
		self.__LogMessage(f"Title: \"{title.slug}\" (ID: {title.id}). {Text}", MessagesTypes.Error)
		self.__PrintMessage(Text, MessagesTypes.Error)
		if exception: raise ParsingError()

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ ПРЕДУПРЕЖДЕНИЙ <<<<< #
	#==========================================================================================#

	def title_not_found(self, title: "BaseTitle", exception: bool = True):
		"""
		Шаблон предупреждения: тайтл не найден.
			title – данные тайтла;\n
			exception – указывает, выбрасывать ли исключение.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param exception: Указывает, следует ли выбросить исключение.
		:type exception: bool
		:raises TitleNotFound: Выбрасывается при активации соответствующего аргумента.
		"""

		NoteID = f" (ID: {title.id})" if title.id else ""
		Text = f"Title: \"{title.slug}\"{NoteID}. Not found."

		if self.__LoggerSettings.telebot.rules.title_not_found:
			self.__SendReport(Text)
			self.__SilentMode = True

		self.__LogMessage(Text, MessagesTypes.Warning)
		self.__PrintMessage("Title not found.", MessagesTypes.Warning)
		self.__SilentMode = False
		if exception: raise TitleNotFound(title)

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ СООБЩЕНИЙ <<<<< #
	#==========================================================================================#

	def amending_end(self, title: 'BaseTitle', amended_chapter_count: int):
		"""
		Шаблон сообщения: дополнение глав завершено.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param amended_chapter_count: Количество дополненных глав.
		:type amended_chapter_count: int
		"""

		self.__LogMessage(f"Title: \"{title.slug}\" (ID: {title.id}). Amended chapters count: {amended_chapter_count}.")
		self.__PrintMessage(f"Amended chapters count: {amended_chapter_count}.")

	def chapter_amended(self, title: "BaseTitle", chapter: "BaseChapter"):
		"""
		Шаблон сообщения: глава дополнена.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param chapter: Данные главы.
		:type chapter: BaseChapter
		"""

		ChapterNote = "Paid chapter" if chapter.is_paid else "Chapter"
		self.__LogMessage(f"Title: \"{title.slug}\" (ID: {title.id}). {ChapterNote} {chapter.id} amended.")
		self.__PrintMessage(f"{ChapterNote} {chapter.id} amended.")

	def chapter_repaired(self, title: "BaseTitle", chapter: "BaseChapter"):
		"""
		Шаблон сообщения: глава восстановлена.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param chapter: Данные главы.
		:type chapter: BaseChapter
		"""

		ChapterNote = "Paid chapter" if chapter.is_paid else "Chapter"
		self.__LogMessage(f"Title: \"{title.slug}\" (ID: {title.id}). {ChapterNote} {chapter.id} repaired.")
		self.__PrintMessage(f"{ChapterNote} {chapter.id} repaired.")
		
	def header(self, header: str, stdout: bool = True, log: bool = True):
		"""
		Шаблон сообщения: заголовок.

		:param header: Текст заголовка.
		:type header: str
		:param stdout: Указывает, выводить ли данные в консоль.
		:type stdout: bool
		:param log: Указывает, записывать ли данные в логи.
		:type log: bool
		"""

		header = header.upper()
		header = f"===== {header} ====="
		if stdout: self.__PrintMessage(header)
		if log: self.__LogMessage(header)

	def merging_end(self, title: "BaseTitle", merged_chapter_count: int):
		"""
		Шаблон сообщения: объединение данных завершено.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param merged_chapter_count: Количество полученных при слиянии глав.
		:type merged_chapter_count: int
		"""

		if self.__SystemObjects.FORCE_MODE:
			self.__LogMessage(f"Title: \"{title.slug}\" (ID: {title.id}). Local data will be removed.")
			self.__PrintMessage("Local data will be removed.")

		else:
			self.__LogMessage(f"Title: \"{title.slug}\" (ID: {title.id}). Merged chapters count: {merged_chapter_count}.")
			self.__PrintMessage(f"Merged chapters count: {merged_chapter_count}.")

	def parsing_start(self, title: "BaseTitle", index: int, titles_count: int):
		"""
		Шаблон сообщения: парсинг начат.

		:param title: Данные тайтла.
		:type title: BaseTitle
		:param index: Индекс текущей операции парсинга.
		:type index: int
		:param titles_count: Количество тайтлов.
		:type titles_count: int
		"""

		NoteID = f" (ID: {title.id})" if title.id else ""
		self.__LogMessage(f"Title: \"{title.slug}\"{NoteID}. Parsing...")
		if titles_count > 1: Templates.ParsingProgress(index, titles_count)
		self.__PrintMessage(f"Parsing <b>{title.slug}</b>{NoteID}...")

	def titles_collected(self, count: int):
		"""
		Шаблон сообщения: коллекция собрана.

		:param count: Количество добавленных в коллекцию тайтлов.
		:type count: int
		"""

		self.__LogMessage(f"Collected titles count: {count}.")
		self.__PrintMessage(f"Titles collected: {count}.")

	#==========================================================================================#
	# >>>>> МЕТОДЫ УПРАВЛЕНИЯ ЛОГАМИ <<<<< #
	#==========================================================================================#

	def close(self):
		"""Закрывает логи."""

		if not self.__LoggerRule: self.set_rule(self.__LoggerSettings.cleaner[self.__PointName])

		logging.shutdown()

		IsClean = False

		if self.__LoggerRule == LoggerRules.Remove: IsClean = True
		if self.__LoggerRule == LoggerRules.SaveIfHasErrors and not self.__IsLogHasError: IsClean = True
		if self.__LoggerRule == LoggerRules.SaveIfHasWarnings and not self.__IsLogHasWarning and not self.__IsLogHasError: IsClean = True

		if IsClean and os.path.exists(self.__LogFilename): os.remove(self.__LogFilename)

		try: os.rmdir("Logs")
		except: pass