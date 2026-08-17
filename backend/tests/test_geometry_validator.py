from app.agent.tools import GeometryError
from app.models.ir import BuildingElement
from app.rules.geometry_validator import validate_elements


def _element(**overrides):
    base = dict(
        id="el-1", type="corridor", page=1, bbox=[0.0, 0.0, 10.0, 10.0],
        geometry={"width_mm": 1500}, source="vlm", confidence=0.9,
    )
    base.update(overrides)
    return BuildingElement(**base)


def test_valid_element_passes_through():
    element = _element()
    valid, errors = validate_elements([element])
    assert valid == [element]
    assert errors == []


def test_inverted_bbox_is_rejected():
    element = _element(bbox=[10.0, 10.0, 0.0, 0.0])
    valid, errors = validate_elements([element])
    assert valid == []
    assert errors == [
        GeometryError(
            element_id="el-1",
            error_type="inverted_bbox",
            message="bbox x_min >= x_max or y_min >= y_max",
        )
    ]


def test_negative_dimension_value_is_rejected():
    element = _element(type="corridor", geometry={"width_mm": -50})
    valid, errors = validate_elements([element])
    assert valid == []
    assert errors[0].error_type == "negative_dimension"


def test_zero_area_bbox_is_rejected():
    element = _element(bbox=[5.0, 5.0, 5.0, 12.0])
    valid, errors = validate_elements([element])
    assert valid == []
    assert errors[0].error_type == "zero_area_bbox"
