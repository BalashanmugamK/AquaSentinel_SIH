import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AgentAskRequest, AgentAskResponse
from app.agent.agent import InvestigationAgent

logger = logging.getLogger("aquasentinel.api.agent")
router = APIRouter(prefix="/api/agent", tags=["AI Investigation Agent"])


@router.post(
    "/ask",
    response_model=AgentAskResponse,
    summary="Ask the AI Water Intelligence Agent (invoked by n8n or direct chat)",
)
def ask_agent(request: AgentAskRequest, db: Session = Depends(get_db)):
    try:
        response = InvestigationAgent.ask(db, request)
        return response
    except Exception as e:
        logger.error(f"Error executing agent investigation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent investigation failed: {str(e)}",
        )
