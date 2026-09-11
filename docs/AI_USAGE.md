# AI / Tool Usage Declaration — FinSight AI

## Purpose

FinSight AI uses AI for document understanding and deterministic Python logic for financial reconciliation. The two responsibilities are intentionally separated.

## AI-assisted capabilities

### Groq-based extraction

The backend uses the Groq API with:

```text
Model: openai/gpt-oss-20b
```

The model is used to interpret OCR/native PDF text and produce a structured representation containing:

- document type
- extracted fields
- extracted values
- evidence text
- confidence values when available
- flexible tables and rows

The extraction prompt explicitly instructs the model not to invent missing financial values.

### What AI does not decide

The LLM is not the final authority for arithmetic reconciliation.

The following are handled by deterministic Python logic:

- quantity × unit price checks
- VAT calculations
- subtotal/total reconciliation
- balance-sheet reconciliation
- profit-and-loss reconciliation
- cash-flow reconciliation
- tolerance evaluation
- PASS / FAIL / NOT_APPLICABLE validation status

This separation makes financial checks reproducible and auditable.

## OCR / document-processing tools

The system uses:

- `pypdf` for native/selectable PDF text
- `pdf2image` for converting scanned PDF pages to images
- Tesseract OCR for scanned PDFs and image files
- Pillow for image handling
- Poppler as the PDF rendering dependency used by `pdf2image`

The OCR service first attempts native PDF text extraction. When meaningful text is unavailable, it falls back to OCR.

## Development assistance

AI-assisted development was used during implementation for tasks such as:

- architectural planning
- code drafting and refactoring
- debugging
- API integration guidance
- validator design
- documentation drafting
- test design

All application code should be treated as project code owned and reviewed by the developer. AI output was inspected and adapted to fit the actual repository, sample data, and runtime behavior.

## Validation philosophy

A central design rule is:

```text
AI = interpret and structure
Python = calculate and verify
Database = persist
Frontend = review and present
```

When the available extracted data is insufficient for a financial check, the system can return `NOT_APPLICABLE` rather than inventing operands.

When source values do not reconcile, the system exposes the discrepancy rather than silently changing the extracted values.

## Secrets

AI/API credentials are supplied through environment variables such as:

```env
GROQ_API_KEY=...
DATABASE_URL=...
```

Secrets are not part of the source repository and should never be committed to Git.

## Human review

The frontend surfaces:

- extracted values
- evidence
- confidence
- missing values
- low-confidence fields
- validation status
- calculated vs reported values

This supports reviewer oversight for uncertain or exceptional documents.

## Final responsibility

AI assistance does not replace engineering review, testing, financial controls, or human judgment. The final behavior of the deployed system is determined by the implemented application code, validation rules, configuration, and external service responses.
