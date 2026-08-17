from app.agent.tools import GeometryError
from app.models.ir import BuildingElement

_DIMENSION_KEYS = {"width_mm", "height_mm", "length_mm", "value_mm", "walking_distance_m"}


def validate_elements(elements: list[BuildingElement]) -> tuple[list[BuildingElement], list[GeometryError]]:
    valid: list[BuildingElement] = []
    errors: list[GeometryError] = []
    for element in elements:
        error = _validate_one(element)
        if error is None:
            valid.append(element)
        else:
            errors.append(error)
    return valid, errors


def _validate_one(element: BuildingElement) -> GeometryError | None:
    x_min, y_min, x_max, y_max = element.bbox
    if (x_max - x_min) == 0 or (y_max - y_min) == 0:
        return GeometryError(
            element_id=element.id, error_type="zero_area_bbox", message="bbox has zero width or height",
        )
    if x_min >= x_max or y_min >= y_max:
        return GeometryError(
            element_id=element.id, error_type="inverted_bbox",
            message="bbox x_min >= x_max or y_min >= y_max",
        )
    for key, value in element.geometry.items():
        if key in _DIMENSION_KEYS and isinstance(value, (int, float)) and value < 0:
            return GeometryError(
                element_id=element.id, error_type="negative_dimension",
                message=f"{key} is negative: {value}",
            )
    return None
