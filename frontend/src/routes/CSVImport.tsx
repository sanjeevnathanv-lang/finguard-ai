import React, { useState } from 'react'
import { uploadTransactionsCSV, CSVUploadResponse } from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { useAuth } from '../lib/auth'

interface CSVImportProps {
  onNavigateToTransactions?: () => void
}

export default function CSVImport({ onNavigateToTransactions }: CSVImportProps) {
  const { role } = useAuth()
  const isViewer = role === 'VIEWER'

  const [file, setFile] = useState<File | null>(null)
  const [previewRows, setPreviewRows] = useState<string[][]>([])
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<CSVUploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (selectedFile: File | null) => {
    setError(null)
    setResult(null)
    setPreviewRows([])

    if (!selectedFile) {
      setFile(null)
      return
    }

    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setError('Invalid file format. Please select a comma-separated values (.csv) file.')
      setFile(null)
      return
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setError('File size exceeds 5 MB. Please select a smaller CSV file.')
      setFile(null)
      return
    }

    setFile(selectedFile)

    // Read first few lines for client-side preview
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      if (!text) return
      const lines = text.split(/\r\n|\n/).filter((l) => l.trim().length > 0)
      const preview = lines.slice(0, 6).map((l) => {
        return l.split(',').map((cell) => cell.replace(/^"(.*)"$/, '$1').trim())
      })
      setPreviewRows(preview)
    }
    reader.readAsText(selectedFile.slice(0, 32 * 1024))
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const res = await uploadTransactionsCSV(file)
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'CSV upload failed')
    } finally {
      setUploading(false)
    }
  }

  const downloadSchemaTemplate = () => {
    const csvContent =
      'reference,timestamp,amount,currency,sender_reference,receiver_reference,transaction_type,channel,status\n'

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'finguard_transaction_template.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">CSV Batch Ingestion</h1>
          <p className="text-sm text-slate-500 mt-1">
            Secure schema validation, deduplication, and atomic transactional ingestion.
          </p>
        </div>

        <button
          type="button"
          onClick={downloadSchemaTemplate}
          className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition shadow-sm flex items-center space-x-1.5 self-start md:self-auto"
        >
          <span>↓ Download CSV Template</span>
        </button>
      </div>

      {isViewer && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold">Viewer Access Mode:</span>
            <span>Batch dataset uploading is disabled for Viewer role. Switch to Analyst or Admin to ingest CSV transaction files.</span>
          </div>
          <span className="font-mono text-[10px] bg-amber-100 px-2 py-0.5 rounded border border-amber-300">RBAC Enforced</span>
        </div>
      )}

      {/* Upload Box */}
      <div className="p-8 bg-white border-2 border-dashed border-slate-300 rounded-xl text-center space-y-4 hover:border-blue-400 transition">
        <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xl">
          ↑
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Select or drop a transaction CSV file</h3>
          <p className="text-xs text-slate-500 mt-1">
            Accepted format: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">.csv</code> (Max size: 5 MB, up to 5,000 rows)
          </p>
        </div>

        <div className="flex justify-center items-center space-x-3">
          <label className={`px-4 py-2 text-xs font-semibold rounded-lg transition shadow-sm ${
            isViewer
              ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
              : 'cursor-pointer text-white bg-blue-600 hover:bg-blue-700'
          }`}>
            <span>Browse Computer</span>
            <input
              type="file"
              accept=".csv"
              disabled={isViewer}
              className="hidden"
              onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
            />
          </label>
        </div>

        {file && (
          <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 max-w-md mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-2 truncate">
              <span className="font-semibold truncate">{file.name}</span>
              <span className="text-slate-400">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading || isViewer}
              className={`px-3 py-1 font-semibold rounded flex items-center space-x-1 shrink-0 ml-2 transition ${
                isViewer
                  ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                  : 'text-white bg-emerald-600 hover:bg-emerald-700'
              }`}
            >
              {uploading && <LoadingSpinner />}
              <span>Upload & Ingest</span>
            </button>
          </div>
        )}
      </div>

      {/* Errors */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
          <strong>Validation Notice:</strong> {error}
        </div>
      )}

      {/* Client-side Preview Table */}
      {previewRows.length > 0 && !result && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              CSV Header & First 5 Rows Preview
            </h3>
            <span className="text-[11px] text-slate-400">Client-side Verification</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-200">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-700">
                  {previewRows[0].map((col, idx) => (
                    <th key={idx} className="p-2 border-r border-slate-200 last:border-r-0">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewRows.slice(1).map((row, rIdx) => (
                  <tr key={rIdx} className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50">
                    {row.map((val, cIdx) => (
                      <td key={cIdx} className="p-2 border-r border-slate-200 last:border-r-0 text-slate-600 font-mono text-[11px]">
                        {val || '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Results & Summary */}
      {result && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-sm">
          <div className="flex justify-between items-start border-b border-slate-200 pb-4">
            <div>
              <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">
                Ingestion Completed
              </span>
              <h2 className="text-lg font-bold text-slate-900 mt-1">{result.message}</h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Batch Reference: {result.import_reference} • Duration: {result.duration_ms} ms
              </p>
            </div>
            {onNavigateToTransactions && (
              <button
                type="button"
                onClick={onNavigateToTransactions}
                className="px-3 py-1.5 text-xs font-semibold text-white bg-slate-900 rounded-lg hover:bg-slate-800"
              >
                Inspect in Transaction Table →
              </button>
            )}
          </div>

          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 uppercase font-semibold">Total Rows</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">{result.total_rows}</div>
            </div>
            <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
              <span className="text-xs text-emerald-700 uppercase font-semibold">Imported</span>
              <div className="text-2xl font-bold text-emerald-700 mt-1">{result.imported_rows}</div>
            </div>
            <div className="p-4 bg-rose-50 rounded-lg border border-rose-200">
              <span className="text-xs text-rose-700 uppercase font-semibold">Rejected</span>
              <div className="text-2xl font-bold text-rose-700 mt-1">{result.rejected_rows}</div>
            </div>
          </div>

          {/* Row Errors */}
          {result.errors.length > 0 && (
            <div className="space-y-2 pt-2">
              <h3 className="text-xs font-bold text-rose-800 uppercase tracking-wider">
                Rejected Row Validation Report ({result.errors.length} records)
              </h3>
              <div className="max-h-60 overflow-y-auto border border-rose-200 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-rose-100 text-rose-900 sticky top-0">
                    <tr>
                      <th className="p-2 w-20">Row #</th>
                      <th className="p-2 w-32">Field</th>
                      <th className="p-2">Validation Failure Detail</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-rose-100 text-rose-800 font-mono text-[11px]">
                    {result.errors.map((err, i) => (
                      <tr key={i} className="hover:bg-rose-50/50">
                        <td className="p-2 font-bold">{err.row_number}</td>
                        <td className="p-2 font-semibold">{err.field || 'General'}</td>
                        <td className="p-2">{err.error_message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
