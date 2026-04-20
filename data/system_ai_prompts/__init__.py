from .antitoxic_moderation import prompt as moderation_prompt
from .asuna_coc import prompt as coc_prompt
from .asuna_general import longPrompt as general_prompt
from .asuna_member import prompt as member_prompt
from .asuna_router import AsunaRouterPrompt as asuna_router_prompt
from .asuna_rules import prompt as rules_prompt
from .main_router import RouterPrompt as router_prompt
from .asuna_smertniki import prompt as smertniki_prompt

__all__ = [
	"moderation_prompt",
	"coc_prompt",
	"general_prompt",
	"member_prompt",
	"asuna_router_prompt",
	"rules_prompt",
	"router_prompt",
	"smertniki_prompt",
]

_EXPORTS = {
	"moderation_prompt": (".antitoxic_moderation", "prompt"),
	"coc_prompt": (".asuna_coc", "prompt"),
	"general_prompt": (".asuna_general", "longPrompt"),
	"member_prompt": (".asuna_member", "prompt"),
	"asuna_router_prompt": (".asuna_router", "AsunaRouterPrompt"),
	"rules_prompt": (".asuna_rules", "prompt"),
	"router_prompt": (".main_router", "RouterPrompt"),
	"smertniki_prompt": (".asuna_smertniki", "prompt"),
}


def __getattr__(name: str):
	target = _EXPORTS.get(name)
	if target is None:
		raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

	module_path, attr_name = target
	module = __import__(f"{__name__}{module_path}", fromlist=[attr_name])
	value = getattr(module, attr_name)
	globals()[name] = value
	return value


def __dir__():
	return sorted(set(globals()) | set(__all__))