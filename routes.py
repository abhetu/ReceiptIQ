from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Receipt, BankTransaction, ReconciliationMatch, MatchStatus
from app.services.receipt_parser import parse_receipt_with_gpt
from app.services.csv_parser import parse_bank_csv
from app.services.reconciliation import run_reconciliation
from app.services.ai_explainer import explain_flagged_match, explain_unmatched_transaction
from datetime import datetime

router = APIRouter()


def serialize_receipt(receipt: Receipt) -> dict:
    return {
        "id": receipt.id,
        "filename": receipt.filename,
        "vendor": receipt.vendor,
        "amount": receipt.amount,
        "date": str(receipt.date) if receipt.date else None,
        "category": receipt.category,
        "confidence": str(receipt.confidence) if receipt.confidence else None,
        "notes": receipt.notes,
    }


def serialize_transaction(txn: BankTransaction) -> dict:
    return {
        "id": txn.id,
        "description": txn.description,
        "amount": txn.amount,
        "txn_date": str(txn.txn_date) if txn.txn_date else None,
    }


# ─── RECEIPTS ─────────────────────────────────────────────────────────────────

@router.post("/receipts/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse a single receipt (image or PDF)."""
    if not file.filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
        raise HTTPException(400, "Supported formats: PDF, JPG, PNG")

    file_bytes = await file.read()

    # AI call: extract structured data from receipt
    try:
        parsed = parse_receipt_with_gpt(file_bytes, file.filename)
    except Exception as exc:
        raise HTTPException(502, f"Receipt extraction failed: {str(exc)}")

    # Parse date string to date object
    receipt_date = None
    if parsed.get("date"):
        try:
            receipt_date = datetime.strptime(parsed["date"], "%Y-%m-%d").date()
        except ValueError:
            pass

    receipt = Receipt(
        filename=file.filename,
        vendor=parsed.get("vendor"),
        amount=parsed.get("amount"),
        date=receipt_date,
        category=parsed.get("category"),
        confidence=parsed.get("confidence", "MEDIUM"),
        raw_text=parsed.get("raw_text", ""),
        notes=parsed.get("notes", ""),
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return serialize_receipt(receipt)


@router.get("/receipts")
def get_receipts(db: Session = Depends(get_db)):
    receipts = db.query(Receipt).all()
    return [serialize_receipt(r) for r in receipts]


@router.delete("/receipts/{receipt_id}")
def delete_receipt(receipt_id: int, db: Session = Depends(get_db)):
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(404, "Receipt not found")
    db.delete(receipt)
    db.commit()
    return {"status": "deleted"}


# ─── BANK TRANSACTIONS ────────────────────────────────────────────────────────

@router.post("/transactions/upload")
async def upload_bank_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload bank statement CSV."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file")

    file_bytes = await file.read()

    try:
        transactions = parse_bank_csv(file_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))

    created = []
    for txn in transactions:
        t = BankTransaction(**txn)
        db.add(t)
        created.append(t)

    db.commit()
    return {"imported": len(created), "transactions": created}


@router.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    txns = db.query(BankTransaction).all()
    return [serialize_transaction(t) for t in txns]


# ─── RECONCILIATION ───────────────────────────────────────────────────────────

@router.post("/reconcile")
def run_reconcile(db: Session = Depends(get_db)):
    """
    Run reconciliation engine. Core algorithm is in services/reconciliation.py.
    AI is only called for explaining flagged/unmatched items.
    """
    receipts = db.query(Receipt).all()
    transactions = db.query(BankTransaction).all()

    if not receipts:
        raise HTTPException(400, "No receipts uploaded yet")
    if not transactions:
        raise HTTPException(400, "No bank transactions uploaded yet")

    # Run YOUR reconciliation algorithm (no AI)
    try:
        result = run_reconciliation(receipts, transactions)
    except Exception as exc:
        raise HTTPException(500, f"Reconciliation failed: {str(exc)}")

    # Save matches to DB
    for match_data in result["matched"]:
        match = ReconciliationMatch(
            receipt_id=match_data["receipt"].id,
            transaction_id=match_data["transaction"].id,
            score=match_data["score"],
            status=MatchStatus.MATCHED,
        )
        db.add(match)

    # For flagged matches, call AI to explain WHY it's uncertain
    flagged_with_explanations = []
    for match_data in result["flagged"]:
        explanation = explain_flagged_match(
            match_data["receipt"],
            match_data["transaction"],
            match_data["breakdown"]
        )
        match = ReconciliationMatch(
            receipt_id=match_data["receipt"].id,
            transaction_id=match_data["transaction"].id,
            score=match_data["score"],
            status=MatchStatus.FLAGGED,
            explanation=explanation,
        )
        db.add(match)
        db.flush()
        flagged_with_explanations.append({
            "match_id": match.id,
            "receipt": serialize_receipt(match_data["receipt"]),
            "transaction": serialize_transaction(match_data["transaction"]),
            "score": match_data["score"],
            "confidence": match_data.get("confidence", "LOW"),
            "reasons": match_data.get("reasons", []),
            "score_breakdown": match_data["breakdown"],
            "top_candidates": [
                {
                    "transaction": serialize_transaction(candidate["transaction"]),
                    "score": candidate["score"],
                    "confidence": candidate.get("confidence", "LOW"),
                    "reasons": candidate.get("reasons", []),
                    "score_breakdown": candidate.get("breakdown", {}),
                }
                for candidate in match_data.get("top_candidates", [])
            ],
            "explanation": explanation,
        })

    # For unmatched transactions, get AI to decode cryptic bank descriptions
    unmatched_with_explanations = []
    for txn in result["unmatched_transactions"]:
        explanation = explain_unmatched_transaction(txn)
        unmatched_with_explanations.append({
            "transaction": serialize_transaction(txn),
            "explanation": explanation,
        })

    db.commit()

    return {
        "summary": result["summary"],
        "matched": [
            {
                "receipt": serialize_receipt(m["receipt"]),
                "transaction": serialize_transaction(m["transaction"]),
                "score": m["score"],
                "confidence": m.get("confidence", "MEDIUM"),
                "reasons": m.get("reasons", []),
                "score_breakdown": m.get("breakdown", {}),
            }
            for m in result["matched"]
        ],
        "flagged": flagged_with_explanations,
        "unmatched_receipts": [serialize_receipt(r) for r in result["unmatched_receipts"]],
        "unmatched_transactions": unmatched_with_explanations,
    }


@router.post("/reconcile/confirm/{match_id}")
def confirm_match(match_id: int, db: Session = Depends(get_db)):
    """User confirms a flagged match as correct."""
    match = db.query(ReconciliationMatch).filter(ReconciliationMatch.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match not found")
    match.status = MatchStatus.MATCHED
    db.commit()
    return {"status": "confirmed"}


@router.delete("/reconcile/reject/{match_id}")
def reject_match(match_id: int, db: Session = Depends(get_db)):
    """User rejects a flagged match as incorrect."""
    match = db.query(ReconciliationMatch).filter(ReconciliationMatch.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match not found")
    db.delete(match)
    db.commit()
    return {"status": "rejected"}


# ─── REPORT ───────────────────────────────────────────────────────────────────

@router.get("/report")
def get_report(db: Session = Depends(get_db)):
    """Get expense report grouped by category."""
    receipts = db.query(Receipt).all()
    by_category = {}
    for r in receipts:
        cat = r.category or "Other"
        if cat not in by_category:
            by_category[cat] = {"count": 0, "total": 0.0, "items": []}
        by_category[cat]["count"] += 1
        by_category[cat]["total"] += r.amount or 0
        by_category[cat]["items"].append({
            "vendor": r.vendor,
            "amount": r.amount,
            "date": str(r.date),
            "confidence": str(r.confidence),
        })

    grand_total = sum(v["total"] for v in by_category.values())
    return {"by_category": by_category, "grand_total": grand_total}


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    receipts = db.query(Receipt).order_by(Receipt.id.desc()).all()
    transactions = db.query(BankTransaction).order_by(BankTransaction.id.desc()).all()
    matches = db.query(ReconciliationMatch).all()

    matched_count = sum(1 for m in matches if m.status == MatchStatus.MATCHED)
    flagged_count = sum(1 for m in matches if m.status == MatchStatus.FLAGGED)

    total_receipts = len(receipts)
    total_transactions = len(transactions)
    unmatched_count = max(total_receipts - matched_count - flagged_count, 0)
    total_spend = sum(abs(r.amount or 0) for r in receipts)

    spend_by_category = {}
    for receipt in receipts:
        category = receipt.category or "Other"
        spend_by_category[category] = spend_by_category.get(category, 0) + abs(receipt.amount or 0)

    return {
        "total_receipts": total_receipts,
        "total_transactions": total_transactions,
        "matched_count": matched_count,
        "flagged_count": flagged_count,
        "unmatched_count": unmatched_count,
        "total_spend": total_spend,
        "spend_by_category": spend_by_category,
        "recent_receipts": [serialize_receipt(r) for r in receipts[:10]],
        "recent_transactions": [serialize_transaction(t) for t in transactions[:10]],
    }
