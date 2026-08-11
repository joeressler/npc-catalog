from fastapi import HTTPException, Request, status
from sqlalchemy import select

from app.deps import DbSession
from app.mappers import serialize_relation_type
from app.models import GraphEdge, RelationType
from app.player_access import ensure_campaign_visible, is_player
from app.routers.graphs.shared import campaign_relation_types_router, relation_types_router
from app.schemas import RelationTypeRead, RelationTypeWrite, RelationTypeWritePartial
from app.services.campaigns import get_campaign_or_404
from app.services.graphs import (
    ensure_default_relation_types,
    ensure_unique_relation_type_name,
    get_relation_type_or_404,
    validate_polarity,
)
from app.services.pagination import paginate_select


@campaign_relation_types_router.get("/")
def list_campaign_relation_types(
    campaign_id: int,
    request: Request,
    db: DbSession,
    page: int = 1,
):
    campaign = get_campaign_or_404(db, campaign_id)
    ensure_campaign_visible(campaign, for_player=is_player(request))

    stmt = (
        select(RelationType)
        .where(RelationType.campaign_id == campaign_id)
        .order_by(RelationType.name.asc())
    )

    def serialize(relation_type: RelationType) -> dict:
        return serialize_relation_type(relation_type).model_dump()

    return paginate_select(
        db,
        request,
        stmt,
        page,
        serialize,
        id_column=RelationType.id,
    )


@campaign_relation_types_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=RelationTypeRead,
)
def create_campaign_relation_type(
    campaign_id: int,
    payload: RelationTypeWrite,
    db: DbSession,
):
    get_campaign_or_404(db, campaign_id)
    ensure_default_relation_types(db, campaign_id)
    ensure_unique_relation_type_name(db, campaign_id=campaign_id, name=payload.name)
    polarity = validate_polarity(payload.polarity)

    relation_type = RelationType(
        campaign_id=campaign_id,
        name=payload.name.strip(),
        polarity=polarity,
    )
    db.add(relation_type)
    db.commit()
    return serialize_relation_type(relation_type)


@relation_types_router.patch("/relation-types/{relation_type_id}/", response_model=RelationTypeRead)
def update_relation_type(
    relation_type_id: int,
    payload: RelationTypeWritePartial,
    db: DbSession,
):
    relation_type = get_relation_type_or_404(db, relation_type_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"] is not None:
        ensure_unique_relation_type_name(
            db,
            campaign_id=relation_type.campaign_id,
            name=data["name"],
            exclude_relation_type_id=relation_type.id,
        )
        relation_type.name = data["name"].strip()
    if "polarity" in data and data["polarity"] is not None:
        relation_type.polarity = validate_polarity(data["polarity"])

    db.commit()
    return serialize_relation_type(relation_type)


@relation_types_router.delete(
    "/relation-types/{relation_type_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_relation_type(relation_type_id: int, db: DbSession):
    relation_type = get_relation_type_or_404(db, relation_type_id)
    in_use = db.scalar(
        select(GraphEdge.id).where(GraphEdge.relation_type_id == relation_type_id).limit(1)
    )
    if in_use is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a relation type that is used by graph edges.",
        )
    db.delete(relation_type)
    db.commit()
