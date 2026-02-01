"""API routes for diagram generation."""

from fastapi import APIRouter, Depends, HTTPException

from app.config.logging import get_logger
from app.middleware.auth import get_current_user
from app.schemas.diagram import PseudocodeDiagramRequest, PseudocodeDiagramResponse
from app.services.diagram import generate_pseudocode_diagram

logger = get_logger(__name__)

router = APIRouter(prefix="/api/diagram", tags=["diagram"])


@router.post("/pseudocode", response_model=PseudocodeDiagramResponse)
async def pseudocode_diagram(
    request: PseudocodeDiagramRequest,
    user: dict = Depends(get_current_user),
):
    """Generate a pseudocode flowchart diagram from user code.

    Uses an LLM to translate code into structured pseudocode nodes and edges.
    No caching — regenerated each time.
    """
    try:
        result = await generate_pseudocode_diagram(
            code=request.code,
            language=request.language,
        )
        return result

    except ValueError as e:
        logger.warning("pseudocode_diagram_validation_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except TimeoutError as e:
        logger.warning("pseudocode_diagram_timeout", error=str(e))
        raise HTTPException(status_code=504, detail="LLM request timed out")
    except Exception as e:
        logger.error("pseudocode_diagram_error", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to generate pseudocode diagram"
        )
