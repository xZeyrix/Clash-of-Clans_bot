# def __getattr__(name: str):
# 	if name == "config":
# 		from .config_holder import config
# 		return config
# 	if name == "state":
# 		from .state_holder import state
# 		return state
# 	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["config", "state"]

_EXPORTS = {
	"config": (".config_holder", "config"),
	"state": (".state_holder", "state")
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