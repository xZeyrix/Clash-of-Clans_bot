__all__ = [
    "AdminCheckMiddleware", "AllowedUsersMiddleware", "PauseCheckMiddleware", "DevIdCheckMiddleware",
    "get_clan_info", "get_clan_members", "get_cwl_prep_members", "get_cwl_status", "get_raids", "get_war_status",
    "save_bot_state", "save_smertniki", "load_bot_state", "load_smertniki",
    "search_videos",
    "logger"
]

_EXPORTS = {
    "AdminCheckMiddleware": (".middlewares", "AdminCheckMiddleware"),
    "AllowedUsersMiddleware": (".middlewares", "AllowedUsersMiddleware"),
    "PauseCheckMiddleware": (".middlewares", "PauseCheckMiddleware"),
    "DevIdCheckMiddleware": (".middlewares", "DevIdCheckMiddleware"),
    "get_clan_info": (".cocapi_get_info", "get_clan_info"),
    "get_clan_members": (".cocapi_get_info", "get_clan_members"),
    "get_cwl_prep_members": (".cocapi_get_info", "get_cwl_prep_members"),
    "get_cwl_status": (".cocapi_get_info", "get_cwl_status"),
    "get_raids": (".cocapi_get_info", "get_raids"),
    "get_war_status": (".cocapi_get_info", "get_war_status"),
    "save_bot_state": (".json_save_and_load", "save_bot_state"),
    "save_smertniki": (".json_save_and_load", "save_smertniki"),
    "load_bot_state": (".json_save_and_load", "load_bot_state"),
    "load_smertniki": (".json_save_and_load", "load_smertniki"),
    "search_videos": (".youtube_api", "search_videos"),
    "logger": (".logging", "logger"),
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