from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, HTTPException
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
import csv
import io
import re


def create_app() -> FastAPI:
    app = FastAPI(title="Receipt Reconciliation Agent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health_check() -> dict:
        return {"status": "ok"}

    # Optional router loading for compatibility with different project layouts.
    router_loaded = False
    try:
        from app.api.routes import router as api_router  # type: ignore
        app.include_router(api_router)
        router_loaded = True
    except Exception:
        try:
            from routes import router as api_router  # type: ignore
            app.include_router(api_router)
            router_loaded = True
        except Exception:
            # Keep server bootable even when full backend modules are not present
            # in this lightweight repo snapshot.
            pass

    if not router_loaded:
        # Functional fallback endpoints so the frontend can run end-to-end in
        # lightweight/local snapshots missing full app package wiring.
        @dataclass
        class ReceiptRecord:
            id: int
            filename: str
            vendor: Optional[str]
            amount: Optional[float]
            date: Optional[date]
            category: Optional[str]
            confidence: str
            notes: str
            raw_text: str = ""

        @dataclass
        class TransactionRecord:
            id: int
            description: str
            amount: float
            txn_date: Optional[date]

        receipts: list[ReceiptRecord] = []
        transactions: list[TransactionRecord] = []
        matches: list[dict] = []
        next_ids = {"receipt": 1, "txn": 1, "match": 1}

        try:
            from reconciliation import run_reconciliation  # type: ignore
        except Exception:
            run_reconciliation = None

        def serialize_receipt(r: ReceiptRecord) -> dict:
            return {
                "id": r.id,
                "filename": r.filename,
                "vendor": r.vendor,
                "amount": r.amount,
                "date": str(r.date) if r.date else None,
                "category": r.category,
                "confidence": r.confidence,
                "notes": r.notes,
            }

        def serialize_txn(t: TransactionRecord) -> dict:
            return {
                "id": t.id,
                "description": t.description,
                "amount": t.amount,
                "txn_date": str(t.txn_date) if t.txn_date else None,
            }

        def infer_receipt_from_filename(filename: str) -> tuple[str, Optional[float], Optional[date], str]:
            stem = filename.rsplit(".", 1)[0]
            cleaned = stem.replace("_", " ").replace("-", " ").strip()
            vendor = re.sub(r"\d+", "", cleaned).strip().title() or "Unknown Vendor"
            amount_match = re.search(r"(\d+(?:\.\d{1,2})?)", stem)
            amount = float(amount_match.group(1)) if amount_match else None
            date_match = re.search(r"(20\d{2}[-_](?:0[1-9]|1[0-2])[-_](?:0[1-9]|[12]\d|3[01]))", stem)
            parsed_date = None
            if date_match:
                try:
                    parsed_date = datetime.strptime(date_match.group(1).replace("_", "-"), "%Y-%m-%d").date()
                except ValueError:
                    parsed_date = None
            category = "Other"
            lower = vendor.lower()
            if any(k in lower for k in ["starbucks", "chipotle", "uber eats", "restaurant", "cafe"]):
                category = "Food & Dining"
            elif "uber" in lower:
                category = "Travel"
            elif "adobe" in lower or "aws" in lower or "notion" in lower:
                category = "Software & Subscriptions"
            return vendor, amount, parsed_date, category

        @app.get("/dashboard")
        def dashboard_fallback() -> dict:
            matched_count = sum(1 for m in matches if m["status"] == "MATCHED")
            flagged_count = sum(1 for m in matches if m["status"] == "FLAGGED")
            spend_by_category = {}
            for r in receipts:
                cat = r.category or "Other"
                spend_by_category[cat] = spend_by_category.get(cat, 0) + abs(r.amount or 0)
            return {
                "total_receipts": len(receipts),
                "total_transactions": len(transactions),
                "matched_count": matched_count,
                "flagged_count": flagged_count,
                "unmatched_count": max(len(receipts) - matched_count - flagged_count, 0),
                "total_spend": sum(abs(r.amount or 0) for r in receipts),
                "spend_by_category": spend_by_category,
                "recent_receipts": [serialize_receipt(r) for r in receipts[-10:]][::-1],
                "recent_transactions": [serialize_txn(t) for t in transactions[-10:]][::-1],
            }

        @app.get("/report")
        def report_fallback() -> dict:
            by_category = {}
            for r in receipts:
                cat = r.category or "Other"
                if cat not in by_category:
                    by_category[cat] = {"count": 0, "total": 0.0, "items": []}
                by_category[cat]["count"] += 1
                by_category[cat]["total"] += abs(r.amount or 0)
                by_category[cat]["items"].append(
                    {
                        "vendor": r.vendor,
                        "amount": r.amount,
                        "date": str(r.date) if r.date else None,
                        "confidence": r.confidence,
                    }
                )
            return {"by_category": by_category, "grand_total": sum(v["total"] for v in by_category.values())}

        @app.get("/receipts")
        def receipts_fallback() -> list:
            return [serialize_receipt(r) for r in receipts]

        @app.get("/transactions")
        def transactions_fallback() -> list:
            return [serialize_txn(t) for t in transactions]

        @app.post("/receipts/upload")
        async def upload_receipt_fallback(file: UploadFile = File(...)) -> dict:
            if not file.filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
                raise HTTPException(400, "Supported formats: PDF, JPG, PNG")
            vendor, amount, parsed_date, category = infer_receipt_from_filename(file.filename)
            receipt = ReceiptRecord(
                id=next_ids["receipt"],
                filename=file.filename,
                vendor=vendor,
                amount=amount,
                date=parsed_date,
                category=category,
                confidence="LOW",
                notes="Fallback parser inferred fields from filename. Use full backend for GPT extraction.",
            )
            next_ids["receipt"] += 1
            receipts.append(receipt)
            return serialize_receipt(receipt)

        @app.post("/transactions/upload")
        async def upload_txn_fallback(file: UploadFile = File(...)) -> dict:
            if not file.filename.lower().endswith(".csv"):
                raise HTTPException(400, "Please upload a CSV file")
            raw = (await file.read()).decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(raw))
            created = []
            for row in reader:
                desc = row.get("description") or row.get("vendor") or row.get("merchant") or "Unknown transaction"
                amt_raw = row.get("amount") or row.get("txn_amount") or row.get("value") or "0"
                date_raw = row.get("date") or row.get("txn_date") or row.get("transaction_date")
                try:
                    amount = float(str(amt_raw).replace("$", "").replace(",", "").strip())
                except ValueError:
                    amount = 0.0
                parsed_date = None
                if date_raw:
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
                        try:
                            parsed_date = datetime.strptime(str(date_raw).strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                txn = TransactionRecord(
                    id=next_ids["txn"],
                    description=str(desc).strip(),
                    amount=amount,
                    txn_date=parsed_date,
                )
                next_ids["txn"] += 1
                transactions.append(txn)
                created.append(serialize_txn(txn))
            return {"imported": len(created), "transactions": created}

        @app.post("/reconcile")
        def reconcile_fallback() -> dict:
            if not receipts:
                raise HTTPException(400, "No receipts uploaded yet")
            if not transactions:
                raise HTTPException(400, "No bank transactions uploaded yet")
            if run_reconciliation is None:
                raise HTTPException(500, "Reconciliation engine unavailable")

            result = run_reconciliation(receipts, transactions)
            matches.clear()
            flagged_output = []
            for item in result["matched"]:
                matches.append(
                    {
                        "id": next_ids["match"],
                        "status": "MATCHED",
                        "receipt_id": item["transaction"].id,
                        "transaction_id": item["transaction"].id,
                    }
                )
                next_ids["match"] += 1

            for item in result["flagged"]:
                match_id = next_ids["match"]
                next_ids["match"] += 1
                matches.append(
                    {
                        "id": match_id,
                        "status": "FLAGGED",
                        "receipt_id": item["receipt"].id,
                        "transaction_id": item["transaction"].id,
                    }
                )
                flagged_output.append(
                    {
                        "match_id": match_id,
                        "receipt": serialize_receipt(item["receipt"]),
                        "transaction": serialize_txn(item["transaction"]),
                        "score": item["score"],
                        "confidence": item.get("confidence", "LOW"),
                        "reasons": item.get("reasons", []),
                        "score_breakdown": item.get("breakdown", {}),
                        "top_candidates": [
                            {
                                "transaction": serialize_txn(c["transaction"]),
                                "score": c["score"],
                                "confidence": c.get("confidence", "LOW"),
                                "reasons": c.get("reasons", []),
                                "score_breakdown": c.get("breakdown", {}),
                            }
                            for c in item.get("top_candidates", [])
                        ],
                        "explanation": "Fallback mode: deterministic score suggests manual review.",
                    }
                )

            return {
                "summary": result["summary"],
                "matched": [
                    {
                        "receipt": serialize_receipt(m["receipt"]),
                        "transaction": serialize_txn(m["transaction"]),
                        "score": m["score"],
                        "confidence": m.get("confidence", "MEDIUM"),
                        "reasons": m.get("reasons", []),
                        "score_breakdown": m.get("breakdown", {}),
                    }
                    for m in result["matched"]
                ],
                "flagged": flagged_output,
                "unmatched_receipts": [serialize_receipt(r) for r in result["unmatched_receipts"]],
                "unmatched_transactions": [
                    {
                        "transaction": serialize_txn(t),
                        "explanation": "Fallback mode: no matching receipt found.",
                    }
                    for t in result["unmatched_transactions"]
                ],
            }

        @app.post("/reconcile/confirm/{match_id}")
        def confirm_match_fallback(match_id: int) -> dict:
            for m in matches:
                if m["id"] == match_id:
                    m["status"] = "MATCHED"
                    return {"status": "confirmed"}
            raise HTTPException(404, "Match not found")

        @app.delete("/reconcile/reject/{match_id}")
        def reject_match_fallback(match_id: int) -> dict:
            for idx, m in enumerate(matches):
                if m["id"] == match_id:
                    matches.pop(idx)
                    return {"status": "rejected"}
            raise HTTPException(404, "Match not found")

    return app


app = create_app()
