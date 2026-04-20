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