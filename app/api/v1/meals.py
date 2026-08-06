"""
Meal endpoints.

/upload is async because it awaits an external Gemini call (and, for
moderate/unhealthy meals, a FAISS lookup plus a second Gemini call to
compose the reply) — while that's in flight, the event loop is free to
handle other requests instead of a worker thread sitting blocked.
"""

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_meal_service
from app.schemas.meal import MealOut, MealUploadResponse
from app.services.meal_service import MealService

router = APIRouter(prefix="/meals", tags=["meals"])


@router.post("/upload", response_model=MealUploadResponse, status_code=201)
async def upload_meal(
    user_id: int,
    file: UploadFile = File(...),
    service: MealService = Depends(get_meal_service),
):
    image_bytes = await file.read()
    meal, reply = await service.analyze_and_log_meal(user_id, image_bytes)
    return MealUploadResponse(meal=meal, reply=reply)


@router.get("/{user_id}", response_model=list[MealOut])
def get_meal_history(
    user_id: int, limit: int = 50, service: MealService = Depends(get_meal_service)
):
    return service.get_history(user_id, limit)