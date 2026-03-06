import { useState, useEffect } from 'react';
import {
  CheckCircle2, XCircle, Loader2, AlertTriangle,
  ShieldCheck, FileText, Database, ChevronRight,
} from 'lucide-react';

const inputCls =
  'w-full rounded-xl px-4 py-3 text-sm font-dm bg-[#0D1322] border border-white/10 ' +
  'text-white focus:border-[#00D4AA] focus:outline-none focus:ring-1 ' +
  'focus:ring-[#00D4AA] placeholder:text-[#8892A4] transition-colors';

// ── Waiting Period Progress Bar ───────────────────────────────────────────────
function WaitingBar({ served, required }) {
  const pct = Math.min(100, required > 0 ? Math.round((served / required) * 100) : 100);
  const met = served >= required;
  const color = met ? '#00C853' : pct >= 50 ? '#FFD600' : '#FF4757';
  const gap = Math.max(0, required - served);
  return (
    <div className="space-y-1.5 mt-2">
      <div className="flex justify-between text-[11px] font-dm" style={{ color: '#8892A4' }}>
        <span>Waiting Period Progress</span>
        <span style={{ color }}>{pct}%</span>
      </div>
      <div className="w-full h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.08)' }}>
        <div
          className="h-2 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 6px ${color}60` }}
        />
      </div>
      <p className="text-[11px] font-dm" style={{ color }}>
        {served} of {required} days served
        {!met && ` — ${gap} more days needed`}
      </p>
    </div>
  );
}

// ── Single check row ──────────────────────────────────────────────────────────
function CheckRow({ label, check, treatment, isWaiting }) {
  const passed = check?.passed;
  const color = passed ? '#00C853' : '#FF4757';
  return (
    <div
      className="rounded-xl p-4 space-y-1"
      style={{
        background: passed ? 'rgba(0,200,83,0.06)' : 'rgba(255,71,87,0.06)',
        border: `1px solid ${passed ? 'rgba(0,200,83,0.2)' : 'rgba(255,71,87,0.2)'}`,
      }}
    >
      <div className="flex items-center gap-2">
        {passed
          ? <CheckCircle2 size={15} style={{ color, flexShrink: 0 }} />
          : <XCircle size={15} style={{ color, flexShrink: 0 }} />}
        <span className="text-sm font-dm font-semibold" style={{ color: '#F0F4FF' }}>
          {label}
        </span>
      </div>
      {check?.detail && (
        <p className="text-xs font-dm pl-5" style={{ color: '#8892A4' }}>
          {check.detail}
        </p>
      )}
      {isWaiting && (
        <div className="pl-5">
          <WaitingBar served={check?.served_days ?? 0} required={check?.required_days ?? 90} />
        </div>
      )}
    </div>
  );
}

// ── Source badge ──────────────────────────────────────────────────────────────
function SourceBadge({ source }) {
  const fromPDF = source?.pdf_uploaded && source?.insurer_from_pdf;
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] font-dm px-2.5 py-1 rounded-full"
      style={
        fromPDF
          ? { background: 'rgba(0,212,170,0.12)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.25)' }
          : { background: 'rgba(255,255,255,0.07)', color: '#8892A4', border: '1px solid rgba(255,255,255,0.1)' }
      }
    >
      {fromPDF ? <FileText size={10} /> : <Database size={10} />}
      {fromPDF
        ? `Your PDF (${source.insurer_from_pdf})`
        : source?.coverage_source || 'Policy Database'}
    </span>
  );
}

export default function EligibilityChecker() {
  const [form, setForm] = useState({ treatment: '', policy: '', age: '', waiting_period_served_days: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [pdfPolicy, setPdfPolicy] = useState(null);   // from /policy-options
  const [policyOptions, setPolicyOptions] = useState([]); // fallback list
  const [optLoading, setOptLoading] = useState(true);

  // ── Auto-load policy options on mount ────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/api/eligibility/policy-options');
        if (!r.ok) return;
        const data = await r.json();
        setPdfPolicy(data.pdf_policy);
        setPolicyOptions(data.available_policies || []);
        if (data.pdf_policy?.detected && (data.pdf_policy?.insurer || data.pdf_policy?.covered_treatments?.length > 0)) {
          const label = data.pdf_policy.insurer || data.pdf_policy.policy_name || 'Uploaded Policy';
          setForm(f => ({ ...f, policy: label }));
        }
      } catch { /* silently ignore */ }
      finally { setOptLoading(false); }
    })();
  }, []);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleCheck = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch('/api/eligibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          treatment: form.treatment,
          policy: form.policy,
          age: parseInt(form.age, 10),
          waiting_period_served_days: parseInt(form.waiting_period_served_days, 10),
        }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      setResult(await res.json());
    } catch {
      setError('Could not reach backend. Make sure FastAPI server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const allFilled = form.treatment && form.policy && form.age && form.waiting_period_served_days;
  const pdfDetected = pdfPolicy?.detected;

  const checks = result ? [
    { key: 'treatment_covered', label: 'Treatment Covered' },
    { key: 'not_excluded', label: 'Not Excluded' },
    { key: 'waiting_period_met', label: 'Waiting Period Met', isWaiting: true },
    { key: 'age_eligible', label: 'Age Eligible' },
    { key: 'sum_insured_sufficient', label: 'Sum Insured Sufficient' },
  ] : [];

  return (
    <div className="page-enter flex flex-col items-center py-8 px-4">
      <div className="w-full max-w-[680px] space-y-5">
        <div>
          <h2 className="font-syne font-bold text-2xl mb-1" style={{ color: '#F0F4FF' }}>
            Eligibility Checker
          </h2>
          <p className="text-sm font-dm" style={{ color: '#8892A4' }}>
            Check if your treatment is covered — uses your uploaded policy PDF as ground truth
          </p>
        </div>

        {/* Policy context banner */}
        {!optLoading && (
          pdfDetected ? (
            <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-dm"
              style={{ background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.2)', color: '#00D4AA' }}>
              <ShieldCheck size={16} />
              Using your uploaded{' '}
              <strong>{pdfPolicy.policy_name || pdfPolicy.insurer || 'policy'}</strong>
              {' '}as primary source
              {pdfPolicy.covered_treatments?.length > 0 && (
                <span className="ml-1 text-xs opacity-70">
                  ({pdfPolicy.covered_treatments.length} treatments detected)
                </span>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-dm"
              style={{ background: 'rgba(255,214,0,0.07)', border: '1px solid rgba(255,214,0,0.2)', color: '#FFD600' }}>
              <AlertTriangle size={16} />
              No PDF uploaded — using generic policy database. Upload PDF for accurate results.
            </div>
          )
        )}

        {/* Input form */}
        <div className="rounded-2xl p-6 space-y-4"
          style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.35)' }}>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>Your Age</label>
              <input type="number" className={inputCls} placeholder="e.g. 35"
                value={form.age} onChange={set('age')} min={0} max={120} />
            </div>
            <div>
              <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>
                Waiting Period Served (days)
              </label>
              <input type="number" className={inputCls} placeholder="e.g. 120"
                value={form.waiting_period_served_days} onChange={set('waiting_period_served_days')} min={0} />
            </div>
          </div>

          <div>
            <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>Treatment / Procedure</label>
            <input type="text" className={inputCls} placeholder="e.g. Cardiac Surgery"
              value={form.treatment} onChange={set('treatment')} />
          </div>

          <div>
            <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>Policy</label>
            {pdfDetected ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  className={inputCls}
                  value={form.policy}
                  readOnly
                  style={{ opacity: 0.7, cursor: 'not-allowed' }}
                />
                <span className="text-[10px] font-dm px-2 py-1 rounded-full whitespace-nowrap"
                  style={{ background: 'rgba(0,212,170,0.12)', color: '#00D4AA' }}>
                  From PDF
                </span>
              </div>
            ) : (
              <select className={inputCls} value={form.policy} onChange={set('policy')}
                style={{ color: form.policy ? '#F0F4FF' : '#8892A4' }}>
                <option value="" disabled>Select your policy</option>
                {policyOptions.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            )}
          </div>

          <button
            onClick={handleCheck}
            disabled={!allFilled || loading}
            className="w-full flex items-center justify-center gap-2 font-bold rounded-xl px-6 py-3 font-dm transition-all duration-200 disabled:opacity-50"
            style={{ background: '#00D4AA', color: '#0A0F1E' }}
          >
            {loading
              ? <><Loader2 size={17} className="animate-spin" /> Checking…</>
              : <><ChevronRight size={17} /> Check Eligibility</>}
          </button>

          {error && <p className="text-sm font-dm" style={{ color: '#FF4757' }}>{error}</p>}
        </div>

        {/* Result panel */}
        {result && (
          <div className="space-y-4 animate-fade-up">
            {/* Header */}
            <div
              className="rounded-2xl p-5"
              style={{
                background: result.eligible ? 'rgba(0,212,170,0.08)' : 'rgba(255,71,87,0.08)',
                border: `1px solid ${result.eligible ? 'rgba(0,212,170,0.25)' : 'rgba(255,71,87,0.25)'}`,
              }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div style={{ color: result.eligible ? '#00D4AA' : '#FF4757' }}>
                    {result.eligible
                      ? <CheckCircle2 size={40} strokeWidth={1.5} />
                      : <XCircle size={40} strokeWidth={1.5} />}
                  </div>
                  <div>
                    <h3 className="font-syne font-bold text-xl" style={{ color: '#F0F4FF' }}>
                      {result.eligible ? 'You are Eligible' : 'Not Eligible at This Time'}
                    </h3>
                    <p className="text-xs font-dm mt-0.5" style={{ color: '#8892A4' }}>
                      Policy: {result.policy_used === 'Uploaded Policy' ? 'Your Uploaded PDF' : result.policy_used}
                    </p>
                  </div>
                </div>
                <SourceBadge source={result.data_source} />
              </div>
              <p className="text-sm font-dm" style={{ color: '#8892A4' }}>{result.reason}</p>
            </div>

            {/* Per-check breakdown */}
            <div className="space-y-2">
              <p className="text-[10px] font-dm font-semibold uppercase tracking-wider mb-1" style={{ color: '#8892A4' }}>
                Check Breakdown
              </p>
              {checks.map(({ key, label, isWaiting }) => (
                <CheckRow
                  key={key}
                  label={label}
                  check={result.checks[key]}
                  treatment={result.treatment}
                  isWaiting={isWaiting}
                />
              ))}
            </div>

            {/* Warnings */}
            {result.warnings?.length > 0 && (
              <div className="space-y-2">
                <p className="text-[10px] font-dm font-semibold uppercase tracking-wider" style={{ color: '#FFD600' }}>
                  Warnings
                </p>
                {result.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2.5 px-4 py-3 rounded-xl text-sm font-dm"
                    style={{ background: 'rgba(255,214,0,0.07)', border: '1px solid rgba(255,214,0,0.2)', color: '#FFD600' }}>
                    <AlertTriangle size={15} className="shrink-0 mt-0.5" />
                    {w}
                  </div>
                ))}
              </div>
            )}

            {/* Estimated coverage */}
            {result.eligible && result.estimated_coverage_inr && (
              <div className="rounded-xl p-4"
                style={{ background: 'rgba(0,212,170,0.07)', border: '1px solid rgba(0,212,170,0.2)' }}>
                <p className="text-[10px] font-dm font-semibold uppercase tracking-wider mb-2" style={{ color: '#00D4AA' }}>
                  Estimated Coverage
                </p>
                <div className="flex items-end justify-between">
                  <div>
                    <span className="font-syne font-bold text-3xl" style={{ color: '#00D4AA' }}>
                      ₹{result.estimated_coverage_inr.toLocaleString('en-IN')}
                    </span>
                    {result.treatment_info?.avg_cost_inr > 0 && (
                      <p className="text-xs font-dm mt-1" style={{ color: '#8892A4' }}>
                        Based on 85% of estimated treatment cost
                        ₹{result.treatment_info.avg_cost_inr.toLocaleString('en-IN')}
                      </p>
                    )}
                    {result.coverage_note && (
                      <p className="text-xs font-dm mt-0.5" style={{ color: '#8892A4' }}>
                        Note: {result.coverage_note}
                      </p>
                    )}
                  </div>
                  <CheckCircle2 size={36} strokeWidth={1.2} style={{ color: '#00D4AA', opacity: 0.4 }} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
