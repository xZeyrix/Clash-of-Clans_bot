__all__ = [
	"login_coc",
	"close_coc",
	"stop_war_monitor",
	"start_war_monitor",
	"check_war_status",
	"check_cwl_status",
	"get_clan_info",
	"get_war_info",
	"coc_api",
	"monitor",
]

_EXPORTS = {
	"login_coc": (".coc_api", "login_coc"),
	"close_coc": (".coc_api", "close_coc"),
	"stop_war_monitor": (".monitor", "stop_war_monitor"),
	"start_war_monitor": (".monitor", "start_war_monitor"),
	"check_war_status": (".cw_monitor", "check_war_status"),
	"check_cwl_status": (".cwl_monitor", "check_war_status"),
	"get_clan_info": (".clan", "get_clan_info"),
	"get_war_info": (".war", "get_war_info"),
	"coc_api": (".coc_api", None),
	"monitor": (".monitor", None),
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