from typing import Literal

from pydantic import BaseModel

from app.models.ir import BuildingElement


class LayoutBlock(BaseModel):
    model_config = {"frozen": True}

    block_id: str
    page: int
    bbox: list[float]
    block_type: Literal["text", "dimension", "table", "drawing"]
    text: str
    ocr_confidence: float
    dimension_value_mm: float | None = None


def layout_blocks_to_building_elements(blocks: list[LayoutBlock]) -> list[BuildingElement]:
    elements = []
    for block in blocks:
        if block.block_type != "dimension" or block.dimension_value_mm is None:
            continue
        elements.append(
            BuildingElement(
                id=block.block_id,
                type="dimension_annotation",
                page=block.page,
                bbox=block.bbox,
                geometry={"value_mm": block.dimension_value_mm, "raw_text": block.text},
                source="document_ai",
                confidence=block.ocr_confidence,
            )
        )
    return elements
