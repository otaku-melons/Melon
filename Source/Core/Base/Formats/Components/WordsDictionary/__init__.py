from .WordsDictionary import CheckLanguageCode, WordsDictionary

from .Presets.eng import WordsDictionary_eng
from .Presets.rus import WordsDictionary_rus

def GetDictionaryPreset(language_code: str | None) -> WordsDictionary | None:
	"""
	Возвращает готовый словарь локальных определений.

	:param language_code: Код языка по стандарту ISO 639-3.
	:type language_code: str | None
	:return: Пресет словаря для определённого языка.
	:rtype: WordsDictionary | None
	"""

	if not language_code: return
	CheckLanguageCode(language_code)

	return {
		"rus": WordsDictionary_rus,
		"eng": WordsDictionary_eng,
	}[language_code]