"""
Simple synonym map used by search_dictionary.py so a search for a
common everyday word also surfaces the matching insurance term.

Extend this as you notice more synonyms while testing.
"""

SYNONYMS = {
    "premium": ["installment", "instalment", "renewal amount", "payment"],
    "claim": ["compensation", "settlement", "reimbursement"],
    "insured": ["policyholder", "covered person", "customer"],
    "insurer": ["company", "provider", "underwriter"],
    "deductible": ["excess"],
    "exclusion": ["not covered", "excluded"],
    "beneficiary": ["nominee", "recipient"],
    "liability": ["legal responsibility"],
    "endorsement": ["amendment", "policy change"],
}
