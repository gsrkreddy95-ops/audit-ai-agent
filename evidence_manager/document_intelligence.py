"""Document intelligence helpers for the audit AI agent.

The real-world audit workflow contains more than screenshots.  Word reports,
CSVs, PDFs, JSON exports and ad-hoc notes all influence which evidence should
be recollected.  This module centralises rich extraction and LLM-backed
summaries so the brain-first orchestrator can reason about heterogeneous input
with a consistent schema.

The class is intentionally dependency-light: it relies on libraries already in
``requirements.txt`` (PyPDF2, python-docx, pandas, Pillow, pytesseract, PyYAML).
All operations degrade gracefully if an optional dependency fails so the agent
can continue operating even on minimal environments.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # Optional dependency; handled gracefully if unavailable.
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    pd = None

try:  # Optional dependency; handled gracefully if unavailable.
    import PyPDF2  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    PyPDF2 = None

try:  # Optional dependency; handled gracefully if unavailable.
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    pytesseract = None

try:  # Optional dependency; handled gracefully if unavailable.
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    yaml = None

try:  # Optional dependency; handled gracefully if unavailable.
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    Image = None

try:  # Optional dependency; handled gracefully if unavailable.
    from docx import Document as DocxDocument  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    DocxDocument = None


@dataclass
class DocumentInsight:
    """Structured summary returned by :class:`DocumentIntelligence`."""

    file_path: str
    file_name: str
    document_type: str
    content_preview: str
    structured_insights: Dict[str, Any]
    metadata: Dict[str, Any]

    def brief_line(self) -> str:
        """Return a single-line summary useful for prompts or logging."""

        label = self.structured_insights.get("evidence_type") or self.document_type
        recommendation = self.structured_insights.get("recommended_actions")
        if isinstance(recommendation, list):
            recommendation = "; ".join(recommendation[:2])
        elif not isinstance(recommendation, str):
            recommendation = ""

        suffix = f" → {recommendation}" if recommendation else ""
        return f"- {self.file_name} [{label}]{suffix}".strip()


class DocumentIntelligence:
    """Multi-format evidence understanding powered by the LLM brain."""

    def __init__(self, llm=None, max_preview_chars: int = 1200):
        self.llm = llm
        self.max_preview_chars = max_preview_chars
        self._cache: Dict[str, DocumentInsight] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def analyze_document(self, file_path: str, *, metadata: Optional[Dict[str, Any]] = None,
                         context: Optional[str] = None) -> DocumentInsight:
        """Extract rich insights for a given file.

        Args:
            file_path: Local path to the document.
            metadata: Optional metadata from upstream sources (SharePoint, etc.).
            context: Optional natural language context describing the audit ask.
        """

        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")
        cache_key = self._cache_key(path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        document_type = path.suffix.lower().lstrip(".") or "unknown"
        text_content, extraction_meta = self._extract_text(path, document_type)

        structured = self._summarise_with_llm(
            file_name=path.name,
            document_type=document_type,
            text=text_content,
            context=context,
            metadata=metadata or {},
        )

        insight = DocumentInsight(
            file_path=str(path),
            file_name=path.name,
            document_type=document_type,
            content_preview=text_content[: self.max_preview_chars],
            structured_insights=structured,
            metadata={**(metadata or {}), **extraction_meta},
        )

        self._cache[cache_key] = insight
        return insight

    def build_brief_summary(self, files: Iterable[Dict[str, Any]],
                             *, context: Optional[str] = None) -> Tuple[str, List[DocumentInsight]]:
        """Generate a concise bullet summary for a batch of evidence files."""

        bullet_lines: List[str] = []
        insights: List[DocumentInsight] = []

        for file_info in files or []:
            path = self._resolve_from_metadata(file_info)
            if not path or not path.exists():
                name = file_info.get("name") or file_info.get("file_name") or "unknown"
                bullet_lines.append(f"- {name} (unavailable locally)")
                continue

            insight = self.analyze_document(str(path), metadata=file_info, context=context)
            insights.append(insight)
            bullet_lines.append(insight.brief_line())

        if not bullet_lines:
            bullet_lines.append("No previous evidence files available for analysis.")

        return "\n".join(bullet_lines), insights

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------
    def _extract_text(self, path: Path, document_type: str) -> Tuple[str, Dict[str, Any]]:
        """Read a document and return textual representation with metadata."""

        try:
            if document_type in {"png", "jpg", "jpeg", "bmp"}:
                return self._extract_image_text(path)
            if document_type == "pdf":
                return self._extract_pdf_text(path)
            if document_type in {"docx", "doc"}:
                return self._extract_docx_text(path)
            if document_type in {"csv", "tsv"}:
                return self._extract_csv_text(path)
            if document_type in {"xlsx", "xls"}:
                return self._extract_excel_text(path)
            if document_type in {"json"}:
                return self._extract_json_text(path)
            if document_type in {"yml", "yaml"}:
                return self._extract_yaml_text(path)

            # Fallback to plain text read for everything else
            content = path.read_text(encoding="utf-8", errors="ignore")
            return content, {"extraction_strategy": "text"}
        except Exception as exc:  # pragma: no cover - defensive guard
            return f"[extraction failed: {exc}]", {"extraction_error": str(exc)}

    def _extract_pdf_text(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        if not PyPDF2:
            return "", {"extraction_warning": "PyPDF2 not installed", "extraction_strategy": "unavailable"}

        reader = PyPDF2.PdfReader(str(path))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        return "\n".join(pages), {
            "extraction_strategy": "pdf_text",
            "page_count": len(reader.pages),
        }

    def _extract_docx_text(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        if path.suffix.lower() == ".doc":
            return "", {"extraction_warning": "Legacy .doc format not supported"}
        if not DocxDocument:
            return "", {"extraction_warning": "python-docx not installed", "extraction_strategy": "unavailable"}

        document = DocxDocument(str(path))
        paragraphs = [para.text for para in document.paragraphs if para.text.strip()]
        return "\n".join(paragraphs), {
            "extraction_strategy": "docx_text",
            "paragraphs": len(paragraphs),
        }

    def _extract_csv_text(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        if not pd:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return content[:4000], {
                "extraction_strategy": "csv_text_fallback",
                "extraction_warning": "pandas not installed",
            }

        df = pd.read_csv(path)
        preview = df.head().to_string(index=False)
        return (
            f"Columns: {', '.join(df.columns)}\nRows: {len(df)}\nSample:\n{preview}",
            {
                "extraction_strategy": "csv_preview",
                "row_count": len(df),
                "column_count": len(df.columns),
            },
        )

    def _extract_excel_text(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        if not pd:
            return "", {
                "extraction_strategy": "unavailable",
                "extraction_warning": "pandas not installed",
            }

        df = pd.read_excel(path)
        preview = df.head().to_string(index=False)
        return (
            f"Columns: {', '.join(df.columns)}\nRows: {len(df)}\nSample:\n{preview}",
            {
                "extraction_strategy": "excel_preview",
                "row_count": len(df),
                "column_count": len(df.columns),
            },
        )

    def _extract_json_text(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2)[:8000], {"extraction_strategy": "json"}

    def _extract_yaml_text(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        if not yaml:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return content[:4000], {
                "extraction_strategy": "yaml_text_fallback",
                "extraction_warning": "PyYAML not installed",
            }

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2)[:8000], {"extraction_strategy": "yaml"}

    def _extract_image_text(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        if not Image or not pytesseract:
            return "", {
                "extraction_strategy": "unavailable",
                "extraction_warning": "Image OCR dependencies not installed",
            }

        image = Image.open(str(path))
        text = pytesseract.image_to_string(image)
        return text, {"extraction_strategy": "ocr"}

    # ------------------------------------------------------------------
    # LLM summarisation
    # ------------------------------------------------------------------
    def _summarise_with_llm(self, *, file_name: str, document_type: str,
                             text: str, context: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ask the LLM brain for a structured summary."""

        if not text.strip() or not self.llm:
            return {
                "summary": text[:280] if text else "",
                "evidence_type": metadata.get("type") or document_type,
                "recommended_actions": ["Review manually"],
                "confidence": 0.5,
            }

        prompt = f"""You are the audit AI brain that reasons about historical evidence.

DOCUMENT NAME: {file_name}
DOCUMENT TYPE: {document_type}
ADDITIONAL CONTEXT: {context or 'Not provided'}
SOURCE METADATA: {json.dumps(metadata, indent=2)}

CONTENT PREVIEW (trimmed):
"""
        trimmed = text[:4000]
        prompt += trimmed
        prompt += """

Provide a JSON object with:
- evidence_type: concise label for the evidence
- summary: 2-3 sentence explanation of what the file proves
- recommended_actions: ordered list of follow-up evidence to collect this year
- key_entities: list of resource names, accounts or controls mentioned
- risk_signals: list of gaps or stale data observed (empty if none)
- confidence: 0-1 float showing confidence in the assessment
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            cleaned = content.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except Exception:  # pragma: no cover - defensive path
            pass

        return {
            "evidence_type": metadata.get("type") or document_type,
            "summary": trimmed[:280],
            "recommended_actions": ["Review manually"],
            "key_entities": [],
            "risk_signals": [],
            "confidence": 0.4,
        }

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _cache_key(self, path: Path) -> str:
        stat = path.stat()
        return f"{path}:{stat.st_mtime_ns}"

    @staticmethod
    def _resolve_from_metadata(file_info: Dict[str, Any]) -> Optional[Path]:
        """Resolve a local path from heterogeneous metadata dictionaries."""

        candidates = [
            file_info.get("local_path"),
            file_info.get("path"),
            file_info.get("file_path"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            expanded = Path(os.path.expanduser(candidate))
            if expanded.exists():
                return expanded
        return None

