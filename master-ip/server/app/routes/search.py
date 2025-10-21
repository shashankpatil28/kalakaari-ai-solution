# app/routes/search.py
from fastapi import APIRouter, Request, Form, Depends
from typing import Optional

# Import schemas
from app.schemas.search import QuerySchema
from app.constants import TOP_K_DEFAULT

# Import controllers
from app.controllers.search_controller import (
    image_search_url,
    image_search_upsert,
    metadata_search
)

router = APIRouter(
    tags=["Search"]
)

# --- Image Search Routes ---

@router.post("/image-search/url")
async def image_search_url_route(
    image_url: str = Form(...), 
    top_k: int = Form(TOP_K_DEFAULT), 
    include_meta: bool = Form(True)
):
    """
    Provide an image_url (public or signed) and get top-k similar items.
    """
    return await image_search_url(image_url, top_k, include_meta)


@router.post("/image-search/upsert")
async def image_search_upsert_route(
    request: Request,
    craft_id: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)  # accept JSON string in form
):
    """
    Upsert a new image vector + metadata from an image URL and metadata JSON.
    """
    # The 'request' param is not used in the controller, but we keep it
    # in the signature if it's needed later (e.g., for auth).
    return await image_search_upsert(craft_id, image_url, metadata)


# --- Metadata Search Route ---

@router.post("/metadata/search")
def metadata_search_route(payload: QuerySchema):
    """
    Search for items based on textual metadata.
    """
    return metadata_search(payload)