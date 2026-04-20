__all__ = ["admin_router", "user_router", "beta_router"]

_EXPORTS = {
	"admin_router": (".admin", "router"),
	"user_router": (".user", "router"),
	"beta_router": (".beta", "router"),
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