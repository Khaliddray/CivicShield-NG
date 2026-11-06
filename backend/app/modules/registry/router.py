"""Official Information Verification Registry API Endpoints."""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
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
    TrustedSourceCreateRequest,
    TrustedSourceUpdateRequest,
    TrustedSourceOut,
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


@router.post(
    "/sources",
    response_model=APIResponse[TrustedSourceOut],
    status_code=status.HTTP_201_CREATED,
    summary="Register a certified trusted information authority (Officers & Admins)",
)
def create_trusted_source(
    payload: TrustedSourceCreateRequest,
    request: Request,
    current_user: User = Depends(require_permission("registry:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[TrustedSourceOut]:
    """Register trusted electoral information provider (e.g. INEC, Police, Courts)."""
    client_ip = request.client.host if request.client else None
    source = RegistryService.create_trusted_source(
        db=db,
        request=payload,
        registered_by_user_id=current_user.id,
        ip_address=client_ip,
    )
    return APIResponse(
        data=TrustedSourceOut(
            id=source.id,
            name=source.name,
            url=source.url,
            category=source.category,
            verification_status=source.verification_status,
            description=source.description,
            is_active=source.is_active,
            last_retrieved_at=source.last_retrieved_at,
            created_at=source.created_at,
            updated_at=source.updated_at,
            documents_count=len(source.documents) if source.documents else 0,
        ),
        message=f"Trusted authority '{source.name}' registered successfully.",
    )


@router.get(
    "/sources",
    response_model=APIResponse[PaginatedResponse[TrustedSourceOut]],
    summary="List trusted public information authorities (Public & Frontend)",
)
def list_trusted_sources(
    category: Optional[str] = Query(None, description="Filter by category (e.g. ELECTORAL_COMMISSION, LAW_ENFORCEMENT)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[TrustedSourceOut]]:
    """Public registry of authenticated institutional sources supporting civic transparency."""
    skip = (page - 1) * page_size
    sources, total = RegistryService.list_trusted_sources(
        db=db,
        category=category,
        is_active=is_active,
        search_query=search,
        skip=skip,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return APIResponse(
        data=PaginatedResponse(
            items=[
                TrustedSourceOut(
                    id=s.id,
                    name=s.name,
                    url=s.url,
                    category=s.category,
                    verification_status=s.verification_status,
                    description=s.description,
                    is_active=s.is_active,
                    last_retrieved_at=s.last_retrieved_at,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    documents_count=len(s.documents) if s.documents else 0,
                )
                for s in sources
            ],
            pagination=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
        message="Trusted sources retrieved successfully.",
    )


@router.get(
    "/sources/{source_id}",
    response_model=APIResponse[TrustedSourceOut],
    summary="Inspect trusted authority details (Public)",
)
def get_trusted_source(
    source_id: str,
    db: Session = Depends(get_db),
) -> APIResponse[TrustedSourceOut]:
    """Retrieve full details of a trusted institutional source."""
    source = RegistryService.get_trusted_source(db=db, source_id=source_id)
    return APIResponse(
        data=TrustedSourceOut(
            id=source.id,
            name=source.name,
            url=source.url,
            category=source.category,
            verification_status=source.verification_status,
            description=source.description,
            is_active=source.is_active,
            last_retrieved_at=source.last_retrieved_at,
            created_at=source.created_at,
            updated_at=source.updated_at,
            documents_count=len(source.documents) if source.documents else 0,
        ),
        message="Trusted authority details retrieved successfully.",
    )


@router.put(
    "/sources/{source_id}",
    response_model=APIResponse[TrustedSourceOut],
    summary="Update trusted source record (Officers & Admins)",
)
def update_trusted_source(
    source_id: str,
    payload: TrustedSourceUpdateRequest,
    request: Request,
    current_user: User = Depends(require_permission("registry:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[TrustedSourceOut]:
    """Update metadata or verification status of trusted source."""
    client_ip = request.client.host if request.client else None
    source = RegistryService.update_trusted_source(
        db=db,
        source_id=source_id,
        updates=payload,
        modified_by_user_id=current_user.id,
        ip_address=client_ip,
    )
    return APIResponse(
        data=TrustedSourceOut(
            id=source.id,
            name=source.name,
            url=source.url,
            category=source.category,
            verification_status=source.verification_status,
            description=source.description,
            is_active=source.is_active,
            last_retrieved_at=source.last_retrieved_at,
            created_at=source.created_at,
            updated_at=source.updated_at,
            documents_count=len(source.documents) if source.documents else 0,
        ),
        message=f"Trusted authority '{source.name}' updated successfully.",
    )


@router.delete(
    "/sources/{source_id}",
    response_model=APIResponse[dict],
    summary="Deactivate trusted source authority (Officers & Admins)",
)
def delete_trusted_source(
    source_id: str,
    request: Request,
    current_user: User = Depends(require_permission("registry:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    """Soft-delete / deactivate trusted authority."""
    client_ip = request.client.host if request.client else None
    RegistryService.delete_trusted_source(
        db=db,
        source_id=source_id,
        deleted_by_user_id=current_user.id,
        ip_address=client_ip,
    )
    return APIResponse(
        data={"source_id": source_id, "is_active": False},
        message="Trusted authority deactivated successfully.",
    )
