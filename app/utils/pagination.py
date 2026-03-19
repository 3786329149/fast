def page_result(items: list, page: int = 1, page_size: int = 20, total: int | None = None) -> dict:
    return {
        'list': items,
        'page': page,
        'page_size': page_size,
        'total': len(items) if total is None else total,
    }
