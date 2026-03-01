from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ..BaseFormat import BaseChapter, BaseBranch

@dataclass
class ChapterSearchResult:
	branch: "BaseBranch"
	chapter: "BaseChapter"