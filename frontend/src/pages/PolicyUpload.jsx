import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { CloudUpload, CheckCircle2, FileText, X } from 'lucide-react';
import { useUpload } from '../context/UploadContext';

export default function PolicyUpload() {
  const { handleUploadSuccess, resetUpload } = useUpload();
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const handleFile = (f) => {
    if (f && f.type === 'application/pdf') setFile(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    resetUpload();

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error(await res.text() || 'Failed to upload document');

      const data = await res.json();

      // Save extracted text to context (limit size slightly just in case it's huge)
      const extractedText = data?.extracted_text || data?.text || "";
      const content = extractedText.slice(0, 5000);
      const policyName = file.name.replace(/\.[^/.]+$/, "");

      localStorage.setItem(
        'insurance_policy_context',
        `I am attaching my insurance policy document titled '${policyName}'. ` +
        `Here is the extracted text from the PDF:\n\n${content}\n\n` +
        `Please use this specific policy data to answer my next questions.`
      );

      // Save the structured JSON for the dashboard/eligibility functions 
      localStorage.setItem('insurance_pdf_data', JSON.stringify(data));

      setUploaded(true);
      handleUploadSuccess(data);
    } catch (err) {
      setError(err.message || 'Error parsing PDF. Please try a different document.');
    } finally {
      setUploading(false);
    }
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setFile(null);
    setUploaded(false);
    setError('');
  };

  const formatBytes = (b) => b < 1024 * 1024
    ? `${(b / 1024).toFixed(1)} KB`
    : `${(b / 1024 / 1024).toFixed(1)} MB`;

  return (
    <div className="page-enter flex flex-col items-center justify-center min-h-[calc(100vh-64px-48px)] py-12">
      <div
        className="w-full max-w-2xl rounded-2xl p-8 flex flex-col gap-6"
        style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.4)' }}
      >
        {/* Header */}
        <div>
          <h2 className="font-syne font-bold text-2xl mb-1" style={{ color: '#F0F4FF' }}>Upload Your Policy</h2>
          <p className="text-sm font-dm" style={{ color: '#8892A4' }}>Upload a PDF of your insurance policy for AI-powered analysis</p>
        </div>

        {!uploaded ? (
          <>
            {/* Drop zone */}
            <div
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className="relative flex flex-col items-center justify-center rounded-2xl cursor-pointer transition-all duration-200 select-none"
              style={{
                height: 300,
                border: `2px dashed ${dragOver ? '#00D4AA' : 'rgba(0,212,170,0.35)'}`,
                background: dragOver ? 'rgba(0,212,170,0.07)' : 'rgba(0,212,170,0.03)',
              }}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => handleFile(e.target.files[0])}
              />
              <div
                className="flex items-center justify-center rounded-2xl mb-4"
                style={{ width: 72, height: 72, background: 'rgba(0,212,170,0.12)', color: '#00D4AA' }}
              >
                <CloudUpload size={36} />
              </div>
              <p className="font-dm font-semibold text-base mb-1" style={{ color: '#F0F4FF' }}>
                Drop your policy PDF here
              </p>
              <p className="text-sm font-dm" style={{ color: '#8892A4' }}>or click to browse</p>
              <p className="text-xs font-dm mt-3" style={{ color: 'rgba(136,146,164,0.6)' }}>PDF files only • Max 20MB</p>
            </div>

            {/* File pill */}
            {file && (
              <div
                className="flex items-center gap-3 px-4 py-3 rounded-xl"
                style={{ background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.25)' }}
              >
                <FileText size={18} style={{ color: '#00D4AA', shrink: 0 }} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-dm font-medium truncate" style={{ color: '#F0F4FF' }}>{file.name}</p>
                  <p className="text-xs font-dm" style={{ color: '#8892A4' }}>{formatBytes(file.size)}</p>
                </div>
                <button onClick={clearFile} className="p-1 rounded-lg hover:bg-white/10 transition-colors" style={{ color: '#8892A4' }}>
                  <X size={16} />
                </button>
              </div>
            )}

            {/* Upload button */}
            {file && (
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full flex items-center justify-center gap-2 font-bold rounded-xl px-6 py-3 font-dm transition-all duration-200 disabled:opacity-70"
                style={{ background: '#00D4AA', color: '#0A0F1E' }}
              >
                {uploading ? (
                  <>
                    <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    Uploading…
                  </>
                ) : (
                  'Upload Policy'
                )}
              </button>
            )}

            {error && (
              <p className="text-center text-sm font-dm" style={{ color: '#FF4757' }}>
                {error}
              </p>
            )}
          </>
        ) : (
          /* Success state */
          <div className="flex flex-col items-center py-8 gap-4">
            <div className="animate-scale-in" style={{ color: '#00D4AA' }}>
              <CheckCircle2 size={80} strokeWidth={1.5} />
            </div>
            <h3 className="font-syne font-bold text-2xl" style={{ color: '#F0F4FF' }}>Policy uploaded successfully!</h3>
            <p className="font-dm text-sm text-center" style={{ color: '#8892A4' }}>
              Your policy is ready for analysis. Our AI will extract coverage details, exclusions, and more.
            </p>
            <button
              onClick={() => navigate('/chat')}
              className="mt-2 font-bold rounded-xl px-8 py-3 hover:brightness-110 transition font-dm"
              style={{ background: '#00D4AA', color: '#0A0F1E' }}
            >
              Analyze with AI →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
