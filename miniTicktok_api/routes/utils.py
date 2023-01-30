from typing import TypeVar, Generic, List, Optional
from pydantic import Field
from pydantic.generics import GenericModel

DataT = TypeVar('DataT')

ITEMS_PER_PAGE_DEFAULT = 5


class PaginatedList(GenericModel, Generic[DataT]):
    items: List = Field(description='Items of the current page.')
    items_per_page: int = Field(description='The number of items displayed per page.')
    current_page: int = Field(description='The current page.')
    previous_page: Optional[int] = Field(description='Previous page of the paginated list.')
    next_page: Optional[int] = Field(description='Next page of the paginated list.')
    last_page: int = Field(description='The last page of the paginated list.')
    total_items: int = Field(description='Total items in the whole list.')

    @classmethod
    def create_list(
            cls,
            items: List[DataT],
            current_page: int,
            total_items: int,
            items_per_page: int = ITEMS_PER_PAGE_DEFAULT
    ):
        last_page = (total_items // items_per_page) + 1
        next_page = current_page + 1 if current_page < last_page else None
        previous_page = current_page - 1 if current_page > 1 else None

        return cls(
            items=items,
            items_per_page=items_per_page,
            current_page=current_page,
            previous_page=previous_page,
            next_page=next_page,
            last_page=last_page,
            total_items=total_items,
        )
