__all__ = [
	"smertnikiAdd",
	"smertnikiClear",
	"smertnikiRemove",
	"smertniki",
	"send_message",
	"get_navigation_keyboard",
	"RULES_LIST",
	"admin_moderation_handler",
]

_EXPORTS = {
	"smertnikiAdd": (".smertniki", "smertnikiAdd"),
	"smertnikiClear": (".smertniki", "smertnikiClear"),
	"smertnikiRemove": (".smertniki", "smertnikiRemove"),
	"smertniki": (".smertniki", "smertniki"),
	"send_message": (".send", "send_message"),
	"get_navigation_keyboard": (".rules", "get_navigation_keyboard"),
	"RULES_LIST": (".rules", "RULES_LIST"),
	"admin_moderation_handler": (".moderation", "admin_moderation_handler"),
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