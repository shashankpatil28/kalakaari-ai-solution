from fastapi import APIRouter
from app.schemas.craft import OnboardingData, VerificationResponse

# Import the controller functions
from app.controllers.craft_controllers import create_craftid, verify_craftid

router = APIRouter(
    tags=["CraftID"]
)

@router.post("/create")
async def create_craftid_route(data: OnboardingData):
    """
    API endpoint to create a new CraftID and queue it for anchoring.
    """
    return await create_craftid(data)


@router.get("/verify/{public_id}", response_model=VerificationResponse)
async def verify_craftid_route(public_id: str):
    """
    Verify the integrity and anchoring status of a CraftID.
    """
    return await verify_craftid(public_id)