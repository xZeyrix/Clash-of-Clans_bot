__all__ = [
	"ai_moderation",
	"asuna",
	"promptguard",
	"router",
	"voice_to_text",
	"randomReplica",
	"AICheckMessage",
]

_EXPORTS = {
	"ai_moderation": (".groqapi_functions", "ai_moderation"),
	"asuna": (".groqapi_functions", "asuna"),
	"promptguard": (".groqapi_functions", "promptguard"),
	"router": (".groqapi_functions", "router"),
	"voice_to_text": (".groqapi_functions", "voice_to_text"),
	"randomReplica": (".asuna_jailbreak_phrases", "randomReplica"),
	"AICheckMessage": (".asuna_ai", "AICheckMessage"),
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