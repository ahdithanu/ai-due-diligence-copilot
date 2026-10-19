import os
import re
import uuid
import csv
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from backend.domain.schemas import DocumentChunk

class DocumentParserService:
    def __init__(self, chunk_size: int = 800, overlap: int = 150):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def parse_file(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path, document_id)
        elif ext in (".csv", ".tsv"):
            return self._parse_csv(file_path, document_id, delimiter="\t" if ext == ".tsv" else ",")
        elif ext in (".xlsx", ".xlsm"):
            return self._parse_xlsx(file_path, document_id)
        else:
            return self._parse_text(file_path, document_id)

    def _parse_pdf(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        reader = PdfReader(file_path)
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            text = page.extract_text() or ""
            text = self._clean_text(text)
            
            if not text.strip():
                continue

            page_chunks = self._chunk_text(text)
            for chunk_text in page_chunks:
                section_title = self._extract_section_title(chunk_text)
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=global_chunk_idx,
                    content=chunk_text,
                    page_number=page_num,
                    section_title=section_title,
                    char_count=len(chunk_text)
                )
                chunks.append(chunk)
                global_chunk_idx += 1

        return chunks

    def _parse_text(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        text = self._clean_text(text)
        chunks: List[DocumentChunk] = []
        raw_chunks = self._chunk_text(text)

        for idx, chunk_text in enumerate(raw_chunks):
            section_title = self._extract_section_title(chunk_text)
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=idx,
                content=chunk_text,
                page_number=1,
                section_title=section_title,
                char_count=len(chunk_text)
            )
            chunks.append(chunk)

        return chunks

    def _parse_csv(self, file_path: str, document_id: str, delimiter: str = ",") -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = [r for r in reader if any(cell.strip() for cell in r)]

            if not rows:
                return chunks

            header = rows[0]
            batch_size = 25
            global_idx = 0
            for i in range(1, max(len(rows), 2), batch_size):
                batch = rows[i:i + batch_size] if len(rows) > 1 else []
                table_lines = [" | ".join(header), " | ".join(["---"] * max(len(header), 1))]
                for row in batch:
                    padded = row + [""] * max(0, len(header) - len(row))
                    table_lines.append(" | ".join(padded[:len(header)]))

                content = "\n".join(table_lines)
                end_row = min(i + batch_size - 1, len(rows) - 1)
                section_title = f"Spreadsheet Data (Rows {i}-{end_row})" if end_row >= i else "Header Schema"
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=global_idx,
                    content=content,
                    page_number=1,
                    section_title=section_title,
                    char_count=len(content)
                )
                chunks.append(chunk)
                global_idx += 1
        except Exception:
            return self._parse_text(file_path, document_id)

        return chunks

    def _parse_xlsx(self, file_path: str, document_id: str) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                # 1. Read shared strings if present
                shared_strings: List[str] = []
                if "xl/sharedStrings.xml" in z.namelist():
                    tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                    for si in tree.findall(".//{*}si"):
                        t_elems = si.findall(".//{*}t")
                        shared_strings.append("".join(t.text or "" for t in t_elems))

                # 2. Iterate worksheets
                sheet_names = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
                sheet_names.sort()

                global_idx = 0
                for sheet_idx, sheet_name in enumerate(sheet_names):
                    sheet_tree = ET.fromstring(z.read(sheet_name))
                    rows_data: List[List[str]] = []

                    for row in sheet_tree.findall(".//{*}row"):
                        row_cells: List[str] = []
                        for cell in row.findall("{*}c"):
                            cell_type = cell.attrib.get("t")
                            v_elem = cell.find("{*}v")
                            val = ""
                            if v_elem is not None and v_elem.text is not None:
                                raw_v = v_elem.text
                                if cell_type == "s" and raw_v.isdigit():
                                    s_idx = int(raw_v)
                                    val = shared_strings[s_idx] if s_idx < len(shared_strings) else raw_v
                                else:
                                    val = raw_v
                            row_cells.append(val.strip())
                        if any(c for c in row_cells):
                            rows_data.append(row_cells)

                    if not rows_data:
                        continue

                    header = rows_data[0]
                    batch_size = 25
                    for b_start in range(1, max(len(rows_data), 2), batch_size):
                        batch = rows_data[b_start:b_start + batch_size] if len(rows_data) > 1 else []
                        header_line = " | ".join(header)
                        sep_line = " | ".join(["---"] * max(len(header), 1))
                        lines = [f"### Sheet {sheet_idx + 1} Tabular Model", header_line, sep_line]
                        for r in batch:
                            padded = r + [""] * max(0, len(header) - len(r))
                            lines.append(" | ".join(padded[:len(header)]))

                        content = "\n".join(lines)
                        chunk = DocumentChunk(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            chunk_index=global_idx,
                            content=content,
                            page_number=sheet_idx + 1,
                            section_title=f"Financial Model Sheet {sheet_idx + 1}",
                            char_count=len(content)
                        )
                        chunks.append(chunk)
                        global_idx += 1
        except Exception:
            return self._parse_text(file_path, document_id)

        return chunks if chunks else self._parse_text(file_path, document_id)

    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end >= len(text):
                chunks.append(text[start:].strip())
                break
            
            # Try to break at a paragraph or sentence boundary
            break_point = text.rfind("\n\n", start, end)
            if break_point == -1 or break_point <= start:
                break_point = text.rfind(". ", start, end)
            if break_point == -1 or break_point <= start:
                break_point = end

            chunk_content = text[start:break_point].strip()
            if chunk_content:
                chunks.append(chunk_content)
            
            start = max(start + 1, break_point - self.overlap)

        return chunks

    def _clean_text(self, text: str) -> str:
        # Remove null bytes and excessive inline whitespace while preserving paragraph breaks
        text = text.replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    def _extract_section_title(self, text: str) -> str:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return "General Overview"
        first_line = lines[0]
        # If line looks like a header (short, capitalized, or numbered)
        if len(first_line) < 80:
            return first_line
        return first_line[:60] + "..."
