"""Official Information Verification Registry API Endpoints."""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, require_permission
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.common.schemas import APIResponse, PaginatedResponse, PaginationMeta
from backend.app.modules.auth.models import User
from backend.app.modules.registry.schemas import (
    DocumentCreateRequest,
    OfficialDocumentOut,
    OfficialDocumentDetailOut,
    HashVerificationRequest,
    HashVerificationResponse,
)
from backend.app.modules.registry.service import RegistryService

router = APIRouter(prefix="/registry", tags=["Official Verification Registry"])


@router.post(
    "/documents",
    response_model=APIResponse[OfficialDocumentOut],
    status_code=status.HTTP_201_CREATED,
    summary="Publish and certify an official electoral document (Institutional Officers)",
)
def certify_document(
    request_data: DocumentCreateRequest,
    current_user: User = Depends(require_permission("registry:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[OfficialDocumentOut]:
    """Publish an authenticated government or INEC release with canonical SHA-256 fingerprinting."""
    doc = RegistryService.register_document(
        db=db,
        request=request_data,
        authorized_user_id=current_user.id,
    )
    return APIResponse(
        data=OfficialDocumentOut.model_validate(doc),
        message=f"Official document '{doc.document_code}' certified and indexed with hash {doc.sha256_hash[:16]}...",
    )


@router.post(
    "/verify",
    response_model=APIResponse[HashVerificationResponse],
    summary="Verify document authenticity and cryptographic integrity (Public)",
)
def verify_hash(
    request_data: HashVerificationRequest,
    db: Session = Depends(get_db),
) -> APIResponse[HashVerificationResponse]:
    """Public verification service comparing submitted claims or SHA-256 hashes against certified records."""
    result = RegistryService.verify_document_integrity(db=db, request=request_data)
    return APIResponse(
        data=result,
        message="Cryptographic verification analysis completed.",
    )


@router.get(
    "/search",
    response_model=APIResponse[PaginatedResponse[OfficialDocumentOut]],
    summary="Search authenticated announcements registry (Public)",
)
def search_registry(
    q: Optional[str] = Query(None, description="Search keyword in title, summary, or document code"),
    institution: Optional[str] = Query(None, description="Filter by issuing authority (e.g. INEC, Police)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[OfficialDocumentOut]]:
    """Public lookup across certified electoral communications."""
    skip = (page - 1) * page_size
    items, total = RegistryService.search_documents(
        db=db,
        query=q,
        issuing_institution=institution,
        skip=skip,
        limit=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return APIResponse(
        data=PaginatedResponse(
            items=[OfficialDocumentOut.model_validate(d) for d in items],
            pagination=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
        message="Registry search results retrieved successfully.",
    )


@router.get(
    "/documents/{document_code}",
    response_model=APIResponse[OfficialDocumentDetailOut],
    summary="Inspect official document details and version audit history (Public)",
)
def get_document_by_code(
    document_code: str,
    db: Session = Depends(get_db),
) -> APIResponse[OfficialDocumentDetailOut]:
    """Retrieve full certified document record and version history."""
    doc = RegistryService.get_by_code(db=db, document_code=document_code)
    if not doc:
        raise EntityNotFoundException("OfficialDocument", document_code)

    return APIResponse(
        data=OfficialDocumentDetailOut.model_validate(doc),
        message="Official document retrieved successfully.",
    )
