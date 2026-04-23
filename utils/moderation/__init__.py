__all__ = [
	"ModerationSystem",
	"AntiMatMiddleware",
	"AntiSpamMiddleware",
	"regex_fallback_moderation",
	"apply_moderation_result",
]

_EXPORTS = {
	"ModerationSystem": (".moderation", "ModerationSystem"),
	"AntiMatMiddleware": (".antimat", "AntiMatMiddleware"),
	"regex_fallback_moderation": (".antimat", "regex_fallback_moderation"),
	"apply_moderation_result": (".antimat", "apply_moderation_result"),
	"AntiSpamMiddleware": (".antispam", "AntiSpamMiddleware"),
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