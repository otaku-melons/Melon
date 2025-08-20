from Source.Core.Base.Formats.Components import By, ContentTypes
from Source.Core.Base.Builders.MangaBuilder import MangaBuilder
from Source.Core.Base.Parsers.BaseParser import BaseParser
from Source.Core.Development import DevelopmeptAssistant
from Source.Core.SystemObjects import SystemObjects
from Source.Core.Collector import Collector
from Source.Core.Installer import Installer
from Source.CLI.Templates import Templates
from Source.Core.Tagger import Tagger
from Source.Core.Timer import Timer
from Source.Core import Exceptions

from dublib.CLI.Terminalyzer import ParsedCommandData
from dublib.Methods.Filesystem import WriteJSON
from dublib.Engine.Bus import ExecutionStatus

from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING
from time import sleep

if TYPE_CHECKING:
	from Source.Core.Base.Formats.BaseFormat import BaseTitle
	from Source.Core.Base.Formats.Ranobe import Ranobe
	from Source.Core.Base.Formats.Manga import Manga

def com_build_manga(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Строит читаемый контент из описательного файла.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	TimerObject = Timer(start = True)
	system_objects.logger.header("Building")
	BuildSystemName = None

	for MangaBuilderSystem in ("simple", "zip", "cbz"):
		if command.check_flag(MangaBuilderSystem):
			BuildSystemName = MangaBuilderSystem
			break

	Title = system_objects.manager.current_parser_manifest.content_struct
	Title: "Manga | Ranobe" = Title(system_objects)
	Parser: BaseParser = system_objects.manager.launch_parser()
	Title.set_parser(Parser)

	Builder = MangaBuilder(system_objects, Parser)
	Builder.select_build_system(BuildSystemName)
	Builder.enable_sorting_by_volumes(command.check_flag("v"))
	if command.check_key("ch-template"): Builder.set_chapter_name_template(command.get_key_value("ch-template"))
	if command.check_key("vol-template"): Builder.set_volume_name_template(command.get_key_value("vol-template"))

	try: Title.open(command.arguments[0])
	except FileNotFoundError: return

	if command.check_key("chapter"): Builder.build_chapter(Title, command.get_key_value("chapter"))
	elif command.check_key("branch"): Builder.build_branch(Title, command.get_key_value("branch"))
	else: Builder.build_branch(Title)
	TimerObject.done()

def com_collect(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Собирает алиасы тайтлов из каталога и помещает их в список.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	Filters = command.get_key_value("filters") if command.check_key("filters") else None
	PagesCount = int(command.get_key_value("pages")) if command.check_key("pages") else None
	Sort = command.check_flag("sort")
	Period = int(command.get_key_value("period")) if command.check_key("period") else None

	Title = system_objects.manager.current_parser_manifest.content_struct
	Title = Title(system_objects)
	Parser: BaseParser = system_objects.manager.launch_parser()
	CollectedTitlesCount = 0
	Collection = list()
	CollectorObject = Collector(system_objects, merge = system_objects.FORCE_MODE.status)
	system_objects.logger.header("Collecting")
	if system_objects.FORCE_MODE: system_objects.logger.warning("Collection will be overwritten.", stdout = True)

	if command.check_flag("local"):
		TimerObject = Timer()
		TimerObject.start()
		print("Scanning titles... ", end = "", flush = True)
		CollectedTitlesCount = CollectorObject.from_local()
		ElapsedTime = TimerObject.ends()
		print(f"Done in {ElapsedTime}.")

	elif not system_objects.manager.check_method_collect():
		system_objects.logger.error("Parser doesn't support \"collect\" method.")
		return

	else:
		Collection = Parser.collect(filters = Filters, period = Period, pages = PagesCount)
		CollectedTitlesCount = len(Collection)
		CollectorObject.append(Collection)

	CollectorObject.save(sort = Sort)
	system_objects.logger.titles_collected(CollectedTitlesCount)

def com_get(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Скачивает изображение.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	TimerObject = Timer(start = True)
	Link = command.arguments[0]
	Directory = command.get_key_value("dir") if command.check_key("dir") else system_objects.temper.parser_temp
	Filename = command.get_key_value("name") if command.check_key("name") else None
	FullName = command.check_key("fullname")
	if FullName: Filename = command.get_key_value("fullname")
	system_objects.logger.header("Downloading")
	Parser: BaseParser = system_objects.manager.launch_parser()
	IsImageExists = Parser.images_downloader.is_exists(Link, Directory, Filename, FullName)
	print(f"URL: {command.arguments[0]}")
	if IsImageExists: print("Already exists.")

	if not IsImageExists or system_objects.FORCE_MODE:
		Status = Parser.image(Link)
		if Status: Status += Parser.images_downloader.move_from_temp(Directory, Status.value, Filename, True)
		if IsImageExists: print("Overwritten.")

	TimerObject.done()

def com_help(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Заглушка для обработки помощи.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	pass

def com_init(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Производит установку парсеров.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	Name = command.arguments[0]
	Type = ContentTypes(command.get_key_value("content"))
	system_objects.logger.header("Initializing")
	Assistang = DevelopmeptAssistant(system_objects)

	if command.check_flag("p"): Assistang.init_parser(Name, Type)
	elif command.check_flag("e"):

		if command.check_key("content"):
			system_objects.logger.error("Content specification not supported for extensions.")
			return
		
		Assistang.init_extension(Name)

def com_install(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Производит установку парсеров.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	FullInstallation = command.check_flag("all")
	HaveFalgs = bool(command.flags)
	system_objects.logger.header("Installation")
	print("Running installation...")
	InstallerObject = Installer(system_objects)
	TimerObject = Timer(start = True)

	if not HaveFalgs: 
		print("No installation options.")
		return

	if command.check_flag("a") or FullInstallation: InstallerObject.alias()
	if command.check_flag("r") or FullInstallation: InstallerObject.requirements()
	if command.check_flag("s") or FullInstallation: InstallerObject.scripts()
	if command.check_flag("c") or FullInstallation: InstallerObject.configs()
	if command.check_flag("t") or FullInstallation: InstallerObject.releases()
	TimerObject.done()

def com_list(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Выводит список парсеров в консоль.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	Status = ExecutionStatus()
	TableData = {
		"NAME": [],
		"VERSION": [],
		"TYPE": [],
		"SITE": [],
		"collect": []
	}

	for Parser in system_objects.manager.parsers_names:

		try:
			Manifest = system_objects.manager.get_parser_manifest(Parser)
			TypeName = Manifest.content_struct.__name__.lower()
			TypesEmoji = {
				"anime": "🎬",
				"manga": "🌄",
				"ranobe": "📘"
			}

			# Генерация переменных нужна для отлова исключений до записи в таблицу.
			Version = Manifest.version or ""
			Type = TypesEmoji[TypeName] + " " + Manifest.content_struct.__name__.lower()
			Site = "https://" + Manifest.site
			Collect = system_objects.manager.check_method_collect(Parser)

			TableData["NAME"].append(Parser)
			TableData["VERSION"].append(Version)
			TableData["TYPE"].append(Type)
			TableData["SITE"].append(Site)
			TableData["collect"].append(Collect)

		except Exception as ExceptionData:
			TableData["NAME"].append(Parser)
			TableData["VERSION"].append("")
			TableData["TYPE"].append("")
			TableData["SITE"].append("")
			TableData["collect"].append(None)
			Status.push_error(str(ExceptionData), Parser)

	Templates.parsers_table(TableData)
	Status.print_messages()

def com_parse(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Выполняет парсинг тайтла.

	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	Slugs = list()
	StartIndex = 0
	system_objects.logger.header("Parsing")
	
	ContentType = system_objects.manager.current_parser_manifest.content_struct
	Title: BaseTitle = ContentType(system_objects)
	Parser = system_objects.manager.launch_parser()
	ParserSettings = system_objects.manager.current_parser_settings

	if command.check_flag("last"):

		if not system_objects.CACHING_ENABLED:
			Status = ExecutionStatus()
			Status.push_error("Caching disabled. Last slug unavailable.")
			Status.print_messages()
			return

		if not system_objects.temper.shared_data.last_parsed_slug:
			Status = ExecutionStatus()
			Status.push_error("Last slug undefined. Parse anything firstly.")
			Status.print_messages()
			return
		
		else: Slugs.append(system_objects.temper.shared_data.last_parsed_slug)
			
	elif command.check_flag("collection"):
		Slugs = Collector(system_objects).slugs
		system_objects.logger.info(f"Titles in collection: {len(Slugs)}.")

	elif command.check_flag("updates"):
		Period = int(command.get_key_value("period")) if command.check_key("period") else 24
		print("Collecting updates...")
		Slugs = Parser.collect(period = Period)
		
	elif command.check_flag("local"):
		TimerObject = Timer(start = True)
		print("Scanning titles... ", end = "", flush = True)
		CollectorObject = Collector(system_objects)
		CollectorObject.from_local()
		Slugs += CollectorObject.slugs
		ElapsedTime = TimerObject.ends()
		print(f"Done in {ElapsedTime}.")
		Text = "Local titles to parsing: " + str(len(Slugs)) + "."
		system_objects.logger.info(Text, stdout = True)

	else: Slugs.append(command.arguments[0])
		
	if command.check_key("from"):
		system_objects.logger.info("Processing will be started from slug: \"" + command.get_key_value("from") + "\".")
			
		if command.get_key_value("from") in Slugs: StartIndex = Slugs.index(command.get_key_value("from"))
		else: system_objects.logger.warning("No starting slug in collection. Ignored.")

	ParsedCount = 0
	NotFoundCount = 0
	ErrorsCount = 0
	TotalCount = len(Slugs)

	for Index in range(StartIndex, TotalCount):
		Title = ContentType(system_objects)
		if system_objects.CACHING_ENABLED: system_objects.temper.shared_data.set_last_parsed_slug(Slugs[Index])
		Title.set_slug(Slugs[Index])
		Title.set_parser(Parser)

		try:

			if not system_objects.FORCE_MODE: 
				try: Title.open(Slugs[Index], By.Slug)
				except FileNotFoundError: pass
				
			Title.parse(Index, TotalCount)
			Title.merge()
			Title.amend()
			Title.download_images()
			Title.save(end_timer = True)
			ParsedCount += 1

		except JSONDecodeError as ExceptionData:
			system_objects.logger.error(str(ExceptionData))
			ErrorsCount += 1

		except Exceptions.UnsupportedFormat as ExceptionData:
			system_objects.logger.error(str(ExceptionData))
			ErrorsCount += 1

		except Exceptions.TitleNotFound: NotFoundCount += 1
		except Exceptions.ParsingError: ErrorsCount += 1

		if Index != len(Slugs) - 1: sleep(ParserSettings.common.delay)

	Templates.parsing_summary(ParsedCount, NotFoundCount, ErrorsCount)

def com_repair(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Восстанавливает содержимое главы, заново получая его из источника.
		
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	ChapterID = command.get_key_value("chapter")
	Title: BaseTitle = system_objects.manager.current_parser_manifest.content_struct
	Title = Title(system_objects)
	Parser: BaseParser = system_objects.manager.launch_parser()
	system_objects.logger.header("Repairing")
	Filename = Filename[:-5] if command.arguments[0].endswith(".json") else command.arguments[0]
	system_objects.EXIT_CODE = -1

	try:
		Title.set_parser(Parser)
		Title.open(Filename)
		Title.parse()
		Title.merge()
		Title.repair(ChapterID)
		Title.save(end_timer = True)

	except Exceptions.ChapterNotFound: system_objects.logger.error(f"Chapter with ID {ChapterID} not found in JSON.")
	except FileNotFoundError: system_objects.logger.error(f"File \"{Filename}.json\" not found in titles directory.")
	except (Exceptions.TitleNotFound, Exceptions.ParsingError): pass
	else: system_objects.EXIT_CODE = 0

def com_run(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Восстанавливает содержимое главы, заново получая его из источника.
	
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	ExtensionFullName: str = command.get_key_value("extension", exception = True)
	ParserName, ExtensionName = ExtensionFullName.split("-")
	system_objects.select_parser(ParserName)
	system_objects.select_extension(ExtensionName)
	ExtensionCommand = command.get_key_value("command")

	Extension = system_objects.manager.launch_extension(ParserName, ExtensionName)
	system_objects.logger.header(f"{ParserName}:{ExtensionName}")
	Status: ExecutionStatus = Extension.run(ExtensionCommand)
	Status.print_messages()

def com_tagger(system_objects: SystemObjects, command: ParsedCommandData):
	"""
	Запускает обработчик классификаторов тайтлов.
	
	:param system_objects: Коллекция системных объектов.
	:type system_objects: SystemObjects
	:param command: Данные команды.
	:type command: ParsedCommandData
	"""

	TaggerObject = Tagger()
	Type, Name = TaggerObject.get_classificator_data(command)
	Operation = TaggerObject.process(Name, Type, system_objects.parser_name)

	if command.check_flag("json"): print(Operation.to_json())
	elif command.check_key("file"): WriteJSON(command.get_key_value("file"), Operation.to_dict())
	else: Operation.print()