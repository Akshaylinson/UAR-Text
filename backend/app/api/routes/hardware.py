from __future__ import annotations

from fastapi import APIRouter, Depends

from ...services.hardware_service import HardwareService

router = APIRouter(tags=["hardware"])


def get_hardware_service() -> HardwareService:
    return HardwareService()


@router.get("/api/hardware")
def hardware(service: HardwareService = Depends(get_hardware_service)) -> dict:
    return service.get_hardware_info()

