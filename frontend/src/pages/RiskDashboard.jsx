import { useState, useRef, useEffect } from 'react';
import { Loader2, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useUpload } from '../context/UploadContext';

const R = 80;
const CIRC = 2 * Math.PI * R;

// Maps color names from backend to actual hex colours
const COLOR_MAP = {
  green: '#00C853',
  teal: '#00D4AA',
  yellow: '#FFD600',
  orange: '#FF7043',
  red: '#FF1744',
};

const SEVERITY_STYLE = {
  high: { bg: 'rgba(255,23,68,0.15)', text: '#FF4757', label: 'HIGH' },
  medium: { bg: 'rgba(255,171,0,0.15)', text: '#FFB800', label: 'MED' },
  low: { bg: 'rgba(0,212,170,0.15)', text: '#00D4AA', label: 'LOW' },
};

const BREAKDOWN_LABELS = {
  waiting_period_risk: { label: 'Waiting Period', max: 25 },
  hospital_network_risk: { label: 'Hospital Network', max: 20 },
  coverage_risk: { label: 'Treatment Coverage', max: 25 },
  room_rent_risk: { label: 'Room Rent Cap', max: 15 },
  exclusions_risk: { label: 'Exclusions', max: 15 },
};

function BreakdownBar({ label, score, max }) {
  const pct = Math.round((score / max) * 100);
  const color = pct <= 30 ? '#00D4AA' : pct <= 60 ? '#FFB800' : '#FF4757';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs font-dm" style={{ color: '#8892A4' }}>
        <span>{label}</span>
        <span style={{ color }}>{score}/{max}</span>
      </div>
      <div className="w-full rounded-full h-1.5" style={{ background: 'rgba(255,255,255,0.08)' }}>
        <div
          className="h-1.5 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 6px ${color}80` }}
        />
      </div>
    </div>
  );
}

export default function RiskDashboard() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const circleRef = useRef(null);

  const { pdfUploaded, policyData, getPolicyContext } = useUpload();

  useEffect(() => {
    if (result && circleRef.current) {
      const offset = CIRC * (result.total_score / 100);  // high score = more red fill
      circleRef.current.style.transition = 'stroke-dashoffset 1.2s ease';
      circleRef.current.style.strokeDashoffset = offset;
    }
  }, [result]);

  const handleCalculate = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const ctx = getPolicyContext();

      console.log("[RiskScore] Sending with context:", {
        insurer: ctx?.insurer,
        treatments: ctx?.covered_treatments?.length,
        textChars: ctx?.full_text?.length,
      });

      const res = await fetch('/api/risk-score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          policy_context: ctx,
          policy_text: ctx?.full_text ?? "",
          pdf_policy: ctx,
        }),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.error || 'Could not analyse PDF. Please re-upload your policy document.');
      }
      const data = await res.json();
      console.log("[RiskScore] Result:", data);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Could not reach backend. Make sure FastAPI is running.');
    } finally {
      setLoading(false);
    }
  };

  // Trigger recalculation when policy data loads
  useEffect(() => {
    if (pdfUploaded && policyData) {
      console.log("[RiskScore] PDF data available, calculating...");
      handleCalculate();
    }
  }, [pdfUploaded, policyData]);

  const arcColor = result ? (COLOR_MAP[result.color] || '#00D4AA') : '#00D4AA';
  const hasPolicyContext = pdfUploaded && policyData;

  return (
    <div className="page-enter space-y-6">

      {/* Header card */}
      <div
        className="rounded-2xl p-6 space-y-4"
        style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.35)' }}
      >
        <div>
          <h2 className="font-syne font-bold text-lg" style={{ color: '#F0F4FF' }}>Policy Risk Score</h2>
          <p className="text-xs font-dm mt-0.5" style={{ color: '#8892A4' }}>
            Lower score = safer policy &nbsp;•&nbsp; Powered by Groq AI analysis of your uploaded PDF
          </p>
        </div>

        {hasPolicyContext ? (
          <div className="flex items-center gap-2 text-xs font-dm px-3 py-2 rounded-lg"
            style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.2)' }}>
            <CheckCircle2 size={14} />
            Policy document loaded — AI will analyse your specific policy
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs font-dm px-3 py-2 rounded-lg"
            style={{ background: 'rgba(255,71,87,0.1)', color: '#FF4757', border: '1px solid rgba(255,71,87,0.2)' }}>
            <ShieldAlert size={14} />
            No policy uploaded — upload a PDF on the Upload tab first for accurate results
          </div>
        )}

        <button
          onClick={handleCalculate}
          disabled={loading}
          className="flex items-center gap-2 font-bold rounded-xl px-6 py-3 font-dm transition-all duration-200 disabled:opacity-50"
          style={{ background: '#00D4AA', color: '#0A0F1E' }}
        >
          {loading
            ? <><Loader2 size={17} className="animate-spin" /> Analysing Policy…</>
            : 'Analyse Policy Risk'}
        </button>
        {error && (
          <div className="flex items-center gap-2 text-sm font-dm px-4 py-3 rounded-lg"
            style={{ background: 'rgba(255,71,87,0.1)', color: '#FF4757', border: '1px solid rgba(255,71,87,0.2)' }}>
            <ShieldAlert size={16} />
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Score Gauge + Breakdown */}
          <div
            className="flex flex-col items-center gap-6 rounded-2xl p-8"
            style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.35)' }}
          >
            <h2 className="font-syne font-bold text-lg w-full" style={{ color: '#F0F4FF' }}>
              Policy Risk Score
              <span className="text-xs font-dm font-normal ml-2" style={{ color: '#8892A4' }}>Lower = Safer</span>
            </h2>

            {/* Circular Gauge */}
            <div className="relative flex items-center justify-center">
              <svg width="200" height="200" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r={R} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="16" strokeLinecap="round" />
                <circle
                  ref={circleRef}
                  cx="100" cy="100" r={R}
                  fill="none"
                  stroke={arcColor}
                  strokeWidth="16"
                  strokeLinecap="round"
                  strokeDasharray={CIRC}
                  strokeDashoffset={CIRC}
                  transform="rotate(-90 100 100)"
                  style={{ filter: `drop-shadow(0 0 10px ${arcColor}80)` }}
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="font-syne font-bold text-5xl leading-none" style={{ color: '#F0F4FF' }}>{result.total_score}</span>
                <span className="font-dm text-sm mt-1" style={{ color: '#8892A4' }}>/ 100</span>
                <span
                  className="font-dm text-xs mt-2 font-semibold px-2 py-0.5 rounded-full"
                  style={{ background: `${arcColor}25`, color: arcColor }}
                >
                  {result.grade}
                </span>
              </div>
            </div>

            <p className="text-center text-sm font-dm" style={{ color: '#C8D0E0' }}>{result.recommendation}</p>

            {/* Breakdown bars */}
            <div className="w-full space-y-3">
              <p className="text-xs font-dm font-semibold uppercase tracking-wider" style={{ color: '#8892A4' }}>Risk Breakdown</p>
              {Object.entries(result.breakdown).map(([key, val]) => {
                const meta = BREAKDOWN_LABELS[key];
                if (!meta) return null;
                return <BreakdownBar key={key} label={meta.label} score={val} max={meta.max} />;
              })}
            </div>
          </div>

          {/* Risk Factors */}
          <div
            className="rounded-2xl p-6"
            style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.35)' }}
          >
            <h2 className="font-syne font-bold text-lg mb-4" style={{ color: '#F0F4FF' }}>Risk Factors Detected</h2>

            {result.risk_factors.length === 0 ? (
              <div className="flex items-center gap-2 text-sm font-dm px-3 py-3 rounded-xl"
                style={{ background: 'rgba(0,212,170,0.08)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.15)' }}>
                <CheckCircle2 size={16} />
                ✓ No significant risk factors detected in this policy
              </div>
            ) : (
              <div className="space-y-3">
                {result.risk_factors.map((f, i) => {
                  const sev = SEVERITY_STYLE[f.severity] || SEVERITY_STYLE.medium;
                  return (
                    <div
                      key={i}
                      className="p-4 rounded-xl space-y-1.5 transition-colors hover:bg-white/5"
                      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="text-[10px] font-bold font-dm px-2 py-0.5 rounded-full"
                          style={{ background: sev.bg, color: sev.text }}
                        >
                          {sev.label}
                        </span>
                        <span className="text-sm font-dm font-semibold" style={{ color: '#F0F4FF' }}>{f.factor}</span>
                      </div>
                      <p className="text-xs font-dm leading-relaxed" style={{ color: '#8892A4' }}>{f.detail}</p>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Policy inputs used */}
            {result.policy_inputs && (
              <div className="mt-6 space-y-2">
                <p className="text-xs font-dm font-semibold uppercase tracking-wider" style={{ color: '#8892A4' }}>Extracted Policy Values</p>
                {[
                  { label: 'Waiting Period', val: `${result.policy_inputs.waiting_period_days} days` },
                  { label: 'Network Hospitals', val: result.policy_inputs.hospital_network_size },
                  { label: 'Treatment Coverage', val: `${result.policy_inputs.treatment_coverage_percent}%` },
                  { label: 'Room Rent Cap', val: result.policy_inputs.room_rent_cap === 0 ? 'No cap' : `₹${result.policy_inputs.room_rent_cap.toLocaleString('en-IN')}/day` },
                  { label: 'Exclusions Count', val: result.policy_inputs.exclusions_count },
                ].map(({ label, val }) => (
                  <div key={label} className="flex justify-between text-xs font-dm px-3 py-2 rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.04)', color: '#C8D0E0' }}>
                    <span style={{ color: '#8892A4' }}>{label}</span>
                    <span>{val}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Summary metrics row */}
      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div
            className="rounded-2xl p-5 hover:border-white/10 hover:-translate-y-0.5 transition-all duration-200"
            style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 10px 30px rgba(0,0,0,0.25)' }}
          >
            <p className="font-dm text-xs uppercase tracking-widest mb-2" style={{ color: '#8892A4' }}>Coverage Score</p>
            <p className="font-syne font-bold text-3xl mb-1" style={{ color: '#F0F4FF' }}>
              {result.coverage_score}%
            </p>
          </div>
          <div
            className="rounded-2xl p-5 hover:border-white/10 hover:-translate-y-0.5 transition-all duration-200"
            style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 10px 30px rgba(0,0,0,0.25)' }}
          >
            <p className="font-dm text-xs uppercase tracking-widest mb-2" style={{ color: '#8892A4' }}>Claim Likelihood</p>
            <p className="font-syne font-bold text-3xl mb-1" style={{ color: '#F0F4FF' }}>
              {result.claim_likelihood}
            </p>
          </div>
          <div
            className="rounded-2xl p-5 hover:border-white/10 hover:-translate-y-0.5 transition-all duration-200"
            style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 10px 30px rgba(0,0,0,0.25)' }}
          >
            <p className="font-dm text-xs uppercase tracking-widest mb-2" style={{ color: '#8892A4' }}>Policy Grade</p>
            <p className="font-syne font-bold text-3xl mb-1" style={{ color: '#F0F4FF' }}>{result.policy_grade_letter} - {result.policy_grade_label}</p>
          </div>
        </div>
      )}
    </div>
  );
}
