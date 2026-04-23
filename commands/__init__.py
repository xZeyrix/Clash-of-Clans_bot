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


from importlib import import_module

def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_path, attr_name = target
    module = import_module(module_path, package=__name__)
    value = module if attr_name is None else getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
	return sorted(set(globals()) | set(__all__))