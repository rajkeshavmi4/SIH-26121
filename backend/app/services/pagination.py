from math import ceil
from ..schemas.common import PageMeta
def page_meta(page: int, page_size: int, total: int) -> PageMeta:
    return PageMeta(page=page, page_size=page_size, total=total, pages=ceil(total / page_size) if total else 0)
