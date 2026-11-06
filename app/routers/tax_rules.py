from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TaxSlab, User
from ..schemas import TaxSlabUpdate
from ..security import require_roles


router = APIRouter(prefix="/tax-rules", tags=["tax-rules"])


@router.patch("/slabs/{slab_id}")
def update_tax_slab(
    slab_id: str,
    update: TaxSlabUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    original = db.get(TaxSlab, slab_id)

    if original is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax slab not found",
        )

    if update.effective_from <= original.effective_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New effective date must be later than the original effective date",
        )

    if update.effective_from <= date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New tax rule must have a future effective date",
        )

    overlapping = (
        db.query(TaxSlab)
        .filter(
            TaxSlab.regime == original.regime,
            TaxSlab.financial_year == original.financial_year,
            TaxSlab.slab_id != original.slab_id,
            TaxSlab.effective_from == update.effective_from,
            TaxSlab.income_from == original.income_from,
        )
        .first()
    )

    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A slab with this effective date already exists",
        )

    new_slab = TaxSlab(
        slab_id=f"{original.slab_id}-V2",
        regime=original.regime,
        financial_year=original.financial_year,
        income_from=original.income_from,
        income_to=original.income_to,
        rate_percent=update.rate_percent,
        effective_from=update.effective_from,
        note=update.note or "Updated by administrator",
    )

    db.add(new_slab)
    db.commit()
    db.refresh(new_slab)

    return {
        "message": "Tax slab updated successfully",
        "slab_id": new_slab.slab_id,
        "financial_year": new_slab.financial_year,
        "income_from": str(new_slab.income_from),
        "income_to": (
            str(new_slab.income_to)
            if new_slab.income_to is not None
            else None
        ),
        "old_rate_percent": str(original.rate_percent),
        "new_rate_percent": str(new_slab.rate_percent),
        "effective_from": new_slab.effective_from.isoformat(),
        "updated_by": current_user.username,
    }