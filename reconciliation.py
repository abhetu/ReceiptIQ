"""
RECONCILIATION ENGINE - Written entirely by you, no AI.
This is the heart of the project and what makes it impressive to interviewers.

Algorithm:
1. For each receipt, find candidate bank transactions
2. Score each candidate on 3 dimensions: amount, date, vendor name
3. Accept match if score > threshold
4. Flag ambiguous matches for human review
5. Report unmatched on both sides
"""
from datetime import date
from typing import Optional
from rapidfuzz import fuzz
import re

# --- Scoring weights (you designed these, explain them in interview) ---
AMOUNT_WEIGHT = 50   # Amount match is most important
DATE_WEIGHT = 30     # Date is second most important
VENDOR_WEIGHT = 20   # Vendor name is fuzzy, so weighted least

MATCH_THRESHOLD = 65    # Score above this = match
REVIEW_THRESHOLD = 45   # Score between this and MATCH = flag for review

AMOUNT_TOLERANCE = 0.02  # 2% tolerance for amount (handles tax rounding)
DATE_TOLERANCE_DAYS = 2  # Transactions post 1-2 days after purchase


def normalize_vendor(name: str) -> str:
    """
    Normalize vendor names for comparison.
    'CHIPOTLE #1847 03/05' -> 'chipotle'
    'Chipotle Mexican Grill' -> 'chipotle mexican grill'
    """
    if not name:
        return ""
    name = name.lower().strip()
    # Remove store numbers, dates, extra codes
    name = re.sub(r'#\d+', '', name)
    name = re.sub(r'\d{2}/\d{2}', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def score_amount(receipt_amount: float, txn_amount: float) -> float:
    """
    Score amount match. Returns 0-50.
    Exact match = 50. Within tolerance = proportional. Outside = 0.
    """
    if receipt_amount is None or txn_amount is None:
        return 0
    # Use absolute value of transaction (bank CSVs use negative for debits)
    txn_amount = abs(txn_amount)
    receipt_amount = abs(receipt_amount)
    if receipt_amount == 0:
        return 0
    diff_pct = abs(receipt_amount - txn_amount) / receipt_amount
    if diff_pct <= AMOUNT_TOLERANCE:
        return AMOUNT_WEIGHT  # Full score
    elif diff_pct <= 0.10:
        # Partial score for close-ish amounts
        return AMOUNT_WEIGHT * (1 - (diff_pct / 0.10))
    return 0


def score_date(receipt_date: date, txn_date: date) -> float:
    """
    Score date match. Returns 0-30.
    Same day = 30. 1 day off = 20. 2 days off = 10. More = 0.
    Receipts often post to bank 1-2 days later.
    """
    if receipt_date is None or txn_date is None:
        return 0
    days_diff = abs((receipt_date - txn_date).days)
    if days_diff == 0:
        return DATE_WEIGHT
    elif days_diff == 1:
        return DATE_WEIGHT * 0.7
    elif days_diff == DATE_TOLERANCE_DAYS:
        return DATE_WEIGHT * 0.35
    return 0


def score_vendor(receipt_vendor: str, txn_description: str) -> float:
    """
    Score vendor name match using fuzzy string matching. Returns 0-20.
    Uses RapidFuzz partial_ratio to handle partial name matches.
    'Starbucks' matches 'STARBUCKS COFFEE #4521 MOUNTAIN VIEW CA'
    """
    if not receipt_vendor or not txn_description:
        return 0
    norm_receipt = normalize_vendor(receipt_vendor)
    norm_txn = normalize_vendor(txn_description)
    # partial_ratio handles substring matches well
    similarity = fuzz.partial_ratio(norm_receipt, norm_txn) / 100.0
    return VENDOR_WEIGHT * similarity


def reconcile_single(receipt, transactions: list) -> Optional[dict]:
    """
    Match a single receipt against a list of bank transactions.
    Returns the best match with score and status, or None.
    
    This is the core algorithm. Walk through this in your interview.
    """
    if not transactions:
        return None

    candidates = []
    for txn in transactions:
        amount_score = score_amount(receipt.amount, txn.amount)
        date_score = score_date(receipt.date, txn.txn_date)
        vendor_score = score_vendor(receipt.vendor, txn.description)
        total_score = amount_score + date_score + vendor_score

        candidates.append({
            "transaction": txn,
            "score": total_score,
            "breakdown": {
                "amount": amount_score,
                "date": date_score,
                "vendor": vendor_score
            }
        })

    # Sort by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]

    if best["score"] >= MATCH_THRESHOLD:
        return {**best, "status": "MATCHED"}
    elif best["score"] >= REVIEW_THRESHOLD:
        return {**best, "status": "FLAGGED"}  # Needs human review
    return None


def run_reconciliation(receipts: list, transactions: list) -> dict:
    """
    Full reconciliation run. Returns complete report.
    
    Returns:
        matched: list of (receipt, transaction, score) pairs
        flagged: list of uncertain matches needing review
        unmatched_receipts: receipts with no transaction found
        unmatched_transactions: transactions with no receipt
    """
    matched = []
    flagged = []
    unmatched_receipts = []
    used_transaction_ids = set()

    # Sort receipts by confidence so HIGH confidence matches first
    sorted_receipts = sorted(receipts,
        key=lambda r: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(str(r.confidence), 1))

    for receipt in sorted_receipts:
        # Only consider unused transactions (prevent double matching)
        available_txns = [t for t in transactions if t.id not in used_transaction_ids]
        result = reconcile_single(receipt, available_txns)

        if result is None:
            unmatched_receipts.append(receipt)
        elif result["status"] == "MATCHED":
            matched.append(result)
            used_transaction_ids.add(result["transaction"].id)
        elif result["status"] == "FLAGGED":
            flagged.append(result)
            # Don't mark transaction as used — it might match another receipt better

    # Find unmatched transactions
    matched_txn_ids = {r["transaction"].id for r in matched}
    unmatched_transactions = [t for t in transactions
                               if t.id not in matched_txn_ids
                               and t.id not in {r["transaction"].id for r in flagged}]

    return {
        "matched": matched,
        "flagged": flagged,
        "unmatched_receipts": unmatched_receipts,
        "unmatched_transactions": unmatched_transactions,
        "summary": {
            "total_receipts": len(receipts),
            "total_transactions": len(transactions),
            "matched_count": len(matched),
            "flagged_count": len(flagged),
            "unmatched_receipts_count": len(unmatched_receipts),
            "unmatched_transactions_count": len(unmatched_transactions),
        }
    }
