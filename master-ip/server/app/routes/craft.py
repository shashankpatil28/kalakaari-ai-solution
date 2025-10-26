# app/routes/craft.py
from fastapi import APIRouter

# Import schema
from app.schemas.craft import OnboardingData

# Import controller
from app.controllers.craft_controllers import create_craftid

router = APIRouter(
    tags=["CraftID"]
)

@router.post("/create")
async def create_craftid_route(data: OnboardingData):
    """
    API endpoint to create a new CraftID.
    This route calls the controller logic.
    """
    return await create_craftid(data)