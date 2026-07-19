from fastapi import APIRouter

router = APIRouter(prefix="/v1/rules", tags=["rules"])


@router.get("")
def list_rules():
    return []
