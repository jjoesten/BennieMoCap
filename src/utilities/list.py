import logging
logger = logging.getLogger(__name__)
from typing import Any, List

def check_list_values_are_equal(input_list: List[Any]) -> Any:
    unique_values = set(input_list)
    if len(unique_values) == 1:
        unique_values = unique_values.pop()
        logger.debug(f"all values in list are equal to {unique_values}")
        return unique_values
    else:
        raise Exception(f"list values are not equal, list is {input_list}")
        