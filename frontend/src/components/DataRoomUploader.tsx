import React, { useState, useRef } from 'react';
import { DocumentUploadResponse } from '../types';

interface DataRoomUploaderProps {
  investmentId: string;
  companyName: string;
  onUploadSuccess?: (res: DocumentUploadResponse) => void;
}

export const DataRoomUploader: React.FC<DataRoomUploaderProps> = ({
  investmentId,
  companyName,
  onUploadSuccess
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>('PITCH_DECK');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setUploadResult(null);
      setErrorMessage(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadResult(null);
      setErrorMessage(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !investmentId) return;
    setIsUploading(true);
    setErrorMessage(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('doc_type', docType);

      const res = await fetch(`/api/v1/investments/${investmentId}/documents`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to upload and parse document');
      }

      const data: DocumentUploadResponse = await res.json();
      setUploadResult(data);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (onUploadSuccess) onUploadSuccess(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred during upload');
    } finally {
      setIsUploading(false);
    }
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return '📄';
    if (ext === 'xlsx' || ext === 'xls' || ext === 'csv') return '📊';
    return '📝';
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">📁</span>
            <h2 className="text-xl font-bold text-white tracking-tight">Data Room Document Ingestion</h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Live OCR & RAG Indexing
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Upload institutional PDFs, pitch decks, cap tables, or financial spreadsheets for <span className="text-indigo-300 font-medium">{companyName}</span>.
          </p>
        </div>

        {/* Document Type Dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Classification:</label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-medium focus:outline-none focus:border-indigo-500"
          >
            <option value="PITCH_DECK">Pitch Deck / Presentation</option>
            <option value="FINANCIAL_MODEL">Financial Model / P&L (XLSX/CSV)</option>
            <option value="CAP_TABLE">Cap Table & Equity Agreement</option>
            <option value="CUSTOMER_CONTRACT">Customer & Revenue Contract</option>
            <option value="AUDITED_FINANCIALS">Audited Financial Statements</option>
            <option value="LEGAL">Legal & Governance Charter</option>
            <option value="OTHER">Other Diligence Material</option>
          </select>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          dragActive
            ? 'border-indigo-400 bg-indigo-950/40 scale-[1.01]'
            : 'border-slate-700/80 hover:border-indigo-500/60 bg-slate-900/40 hover:bg-slate-900/70'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.xlsx,.xls,.csv,.tsv,.txt,.md"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-2xl">
            📥
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-200">
              Drag and drop your file here, or <span className="text-indigo-400 hover:underline">browse files</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Supports PDF, Excel (.xlsx, .xls), CSV, and Plain Text files up to 50MB
            </p>
          </div>
        </div>
      </div>

      {/* Selected File Card */}
      {selectedFile && (
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getFileIcon(selectedFile.name)}</span>
            <div>
              <p className="text-sm font-semibold text-slate-200">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">
                {(selectedFile.size / 1024).toFixed(1)} KB • Tag: <span className="text-indigo-300 font-mono">{docType}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleUpload();
              }}
              disabled={isUploading}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50 flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Parsing & Indexing...
                </>
              ) : (
                'Upload & Index into Vector RAG'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Upload Error Banner */}
      {errorMessage && (
        <div className="p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-200 text-xs flex items-center gap-2">
          <span>⚠️</span>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Success Ingestion Card */}
      {uploadResult && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold">
              <span>✅</span>
              <span>Document Successfully Ingested & Indexed</span>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase">
              RAG Ready
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs">
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-mono">Filename</span>
              <span className="font-semibold text-slate-200 truncate block">{uploadResult.filename}</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-mono">Chunks Extracted</span>
              <span className="font-bold text-indigo-300">{uploadResult.chunks_extracted} chunks</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-mono">Evidence Records</span>
              <span className="font-bold text-emerald-300">{uploadResult.evidence_extracted} facts</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-mono">Vector Dimension</span>
              <span className="font-bold text-purple-300">384-dim Dense</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
