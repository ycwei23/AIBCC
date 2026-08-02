from app.ingest.document_ai_adapter import LayoutBlock, layout_blocks_to_building_elements


def test_layout_block_valid():
    block = LayoutBlock(
        block_id="block-1",
        page=2,
        bbox=[100.0, 200.0, 300.0, 220.0],
        block_type="dimension",
        text="1200mm",
        ocr_confidence=0.97,
        dimension_value_mm=1200.0,
    )
    assert block.block_type == "dimension"
    assert block.dimension_value_mm == 1200.0


def test_layout_blocks_to_building_elements_converts_dimension_blocks():
    blocks = [
        LayoutBlock(
            block_id="block-1",
            page=2,
            bbox=[100.0, 200.0, 300.0, 220.0],
            block_type="dimension",
            text="1200mm",
            ocr_confidence=0.97,
            dimension_value_mm=1200.0,
        )
    ]
    elements = layout_blocks_to_building_elements(blocks)
    assert len(elements) == 1
    assert elements[0].id == "block-1"
    assert elements[0].type == "dimension_annotation"
    assert elements[0].source == "document_ai"
    assert elements[0].confidence == 0.97
    assert elements[0].geometry["value_mm"] == 1200.0


def test_layout_blocks_to_building_elements_skips_non_dimension_blocks():
    blocks = [
        LayoutBlock(
            block_id="block-2",
            page=1,
            bbox=[0.0, 0.0, 50.0, 10.0],
            block_type="text",
            text="辦公室平面圖",
            ocr_confidence=0.99,
        )
    ]
    assert layout_blocks_to_building_elements(blocks) == []


def test_layout_blocks_to_building_elements_skips_dimension_block_without_value():
    blocks = [
        LayoutBlock(
            block_id="block-3",
            page=1,
            bbox=[0.0, 0.0, 50.0, 10.0],
            block_type="dimension",
            text="不明尺寸",
            ocr_confidence=0.4,
        )
    ]
    assert layout_blocks_to_building_elements(blocks) == []
