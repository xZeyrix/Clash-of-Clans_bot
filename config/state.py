from dataclasses import dataclass, field
from typing import Any, Optional
from utils.moderation.moderation import ModerationSystem

@dataclass
class YoutubeState:
    date: Optional[str] = None
    content: Optional[list] = None

@dataclass
class RuntimeState:
    # /services/ai_system/asuna_ai.py (On/Off)
    ai_enabled: bool = True

    # 2 lists for dev mode beta test
    beta_testers_ids: list[int] = field(default_factory=list)
    beta_banned_ids: list[int] = field(default_factory=list)

    bot_paused: bool = True

    smertniki: list[str] = field(default_factory=list)
    asuna_history: dict[int, list[dict[str, str]]] = field(default_factory=dict)

    # Youtube cache
    youtube_strategies: YoutubeState = field(default_factory=YoutubeState)
    youtube_layouts: YoutubeState = field(default_factory=YoutubeState)

    moderation: Optional[ModerationSystem] = None