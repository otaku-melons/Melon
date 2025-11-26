from Source.Core.SystemObjects import SystemObjects
from Source.CLI.Descriptions import CommandsList
from Source.CLI import Commands

from dublib.Methods.System import CheckPythonMinimalVersion
from dublib.CLI.Terminalyzer import Terminalyzer

import sys

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ <<<<< #
#==========================================================================================#

CheckPythonMinimalVersion(3, 10)

#==========================================================================================#
# >>>>> НАСТРОЙКА ОБРАБОТЧИКА КОМАНД <<<<< #
#==========================================================================================#

Analyzer = Terminalyzer()
Objects = SystemObjects()
Analyzer.helper.enable()
CommandDataStruct = Analyzer.check_commands(CommandsList)

Objects.logger.info(f"Running with Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} on {sys.platform}.", stdout = False)
Objects.logger.info("Command: \"" + " ".join(sys.argv[1:len(sys.argv)]) + "\".", stdout = False)

if CommandDataStruct == None:
	Objects.logger.error("Unknown command!")
	Objects.logger.set_rule(3)
	Objects.logger.close()
	exit()

elif CommandDataStruct.name in ("help", "list", "tagger"): Objects.LIVE_MODE.enable()

if not Objects.LIVE_MODE:
	if "f" in CommandDataStruct.flags: Objects.FORCE_MODE.enable()
	Objects.logger.templates.option_status("Force mode", Objects.FORCE_MODE.status)
	Objects.logger.templates.option_status("Caching", Objects.CACHING_ENABLED.status)

#==========================================================================================#
# >>>>> ОБРАБОТКА КОММАНД <<<<< #
#==========================================================================================#

try:
	Objects.logger.select_cli_point(CommandDataStruct.name)
	if CommandDataStruct.check_key("use"): Objects.select_parser(CommandDataStruct.get_key_value("use"))
	CommandName = CommandDataStruct.name.replace("-", "_")

	Commands
	exec(f"Commands.com_{CommandName}(Objects, CommandDataStruct)")
	
except KeyboardInterrupt: pass

#==========================================================================================#
# >>>>> ЗАВЕРШЕНИЕ РАБОТЫ <<<<< #
#==========================================================================================#

if not Objects.LIVE_MODE: Objects.logger.header("End")
Objects.logger.close()
exit(Objects.EXIT_CODE)