__all__ = [
	"people",
	"BAN_LIGHT",
	"BAN_TRIGGERS",
	"BAN_WORDS",
	"BAN_LONG",
	"ADMIN_TEXT",
	"RULES_CW",
	"RULES_CWL",
	"RULES_EVENTS",
	"RULES_INFO",
	"RULES_MAIN",
	"RULES_PENALTIES",
	"RULES_RAIDS",
	"RULES_ROLES",
	"RULES_SHORT",
	"help_text",
]

_EXPORTS = {
	"people": (".members_info", "people"),
	"BAN_LIGHT": (".toxic_words_list", "BAN_LIGHT"),
	"BAN_TRIGGERS": (".toxic_words_list", "BAN_TRIGGERS"),
	"BAN_WORDS": (".toxic_words_list", "BAN_WORDS"),
	"BAN_LONG": (".toxic_words_list", "BAN_LONG"),
	"ADMIN_TEXT": (".rules_texts", "ADMIN_TEXT"),
	"RULES_CW": (".rules_texts", "RULES_CW"),
	"RULES_CWL": (".rules_texts", "RULES_CWL"),
	"RULES_EVENTS": (".rules_texts", "RULES_EVENTS"),
	"RULES_INFO": (".rules_texts", "RULES_INFO"),
	"RULES_MAIN": (".rules_texts", "RULES_MAIN"),
	"RULES_PENALTIES": (".rules_texts", "RULES_PENALTIES"),
	"RULES_RAIDS": (".rules_texts", "RULES_RAIDS"),
	"RULES_ROLES": (".rules_texts", "RULES_ROLES"),
	"RULES_SHORT": (".rules_texts", "RULES_SHORT"),
	"help_text": (".rules_texts", "help_text"),
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