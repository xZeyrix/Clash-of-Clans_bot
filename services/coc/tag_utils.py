def normalize_clan_tag(raw_tag: str | None, default_tag: str | None = None) -> str | None:
    """Возвращает нормализованный тег клана вида #XXXX или None, если тег не задан."""
    tag = (raw_tag or "").strip()
    if not tag:
        tag = (default_tag or "").strip()
    if not tag:
        return None

    # Иногда тег приходит в URL-формате (%23TAG)
    if tag.lower().startswith("%23"):
        tag = "#" + tag[3:]

    if not tag.startswith("#"):
        tag = "#" + tag

    return tag
