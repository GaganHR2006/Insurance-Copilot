import { useState } from 'react';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

const inputCls = "w-full rounded-xl px-4 py-3 text-sm font-dm bg-[#0D1322] border border-white/10 text-white focus:border-[#00D4AA] focus:outline-none focus:ring-1 focus:ring-[#00D4AA] placeholder:text-[#8892A4] transition-colors";

const ELIGIBLE_ITEMS = [
  'Condition covered under your policy',
  'Hospital is in-network',
  'No active waiting period',
  'Sum insured is sufficient',
];
const NOT_ELIGIBLE_REASONS = [
  'Age exceeds maximum entry limit or pre-existing condition applies',
  'Waiting period may still be active for this condition',
  'Treatment may fall under policy exclusions',
];

export default function EligibilityChecker() {
  const [form, setForm] = useState({ age: '', disease: '', hospital: '', policy: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // null | 'eligible' | 'not-eligible'

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleCheck = () => {
    setLoading(true);
    setResult(null);
    setTimeout(() => {
      const notEligible =
        parseInt(form.age, 10) > 60 ||
        form.disease.toLowerCase().includes('pre-existing');
      setResult(notEligible ? 'not-eligible' : 'eligible');
      setLoading(false);
    }, 1000);
  };

  const allFilled = form.age && form.disease && form.hospital && form.policy;

  return (
    <div className="page-enter flex flex-col items-center py-8 px-4">
      <div className="w-full max-w-[640px] space-y-5">

        {/* Header */}
        <div>
          <h2 className="font-syne font-bold text-2xl mb-1" style={{ color: '#F0F4FF' }}>Eligibility Checker</h2>
          <p className="text-sm font-dm" style={{ color: '#8892A4' }}>Check if your treatment is covered under your policy</p>
        </div>

        {/* Form Card */}
        <div
          className="rounded-2xl p-6 space-y-4"
          style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.35)' }}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>Your Age</label>
              <input
                type="number"
                className={inputCls}
                placeholder="e.g. 35"
                value={form.age}
                onChange={set('age')}
                min={0} max={120}
              />
            </div>
            <div>
              <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>Disease / Condition</label>
              <input
                type="text"
                className={inputCls}
                placeholder="e.g. Type 2 Diabetes"
                value={form.disease}
                onChange={set('disease')}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>Hospital</label>
            <input
              type="text"
              className={inputCls}
              placeholder="e.g. Apollo Mumbai"
              value={form.hospital}
              onChange={set('hospital')}
            />
          </div>

          <div>
            <label className="block text-xs font-dm font-medium mb-1.5" style={{ color: '#8892A4' }}>Policy</label>
            <select
              className={inputCls}
              value={form.policy}
              onChange={set('policy')}
              style={{ color: form.policy ? '#F0F4FF' : '#8892A4' }}
            >
              <option value="" disabled>Select your policy</option>
              {['HDFC Optima Restore', 'Star Comprehensive', 'ICICI iHealth', 'Niva Bupa ReAssure'].map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleCheck}
            disabled={!allFilled || loading}
            className="w-full flex items-center justify-center gap-2 font-bold rounded-xl px-6 py-3 font-dm transition-all duration-200 disabled:opacity-50"
            style={{ background: '#00D4AA', color: '#0A0F1E' }}
          >
            {loading
              ? <><Loader2 size={17} className="animate-spin" /> Checking…</>
              : 'Check Eligibility'
            }
          </button>
        </div>

        {/* Result */}
        {result === 'eligible' && (
          <div
            className="rounded-2xl p-6 animate-fade-up"
            style={{ background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.25)' }}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="animate-scale-in" style={{ color: '#00D4AA' }}>
                <CheckCircle2 size={48} strokeWidth={1.5} />
              </div>
              <div>
                <h3 className="font-syne font-bold text-xl" style={{ color: '#F0F4FF' }}>You are Eligible</h3>
                <span
                  className="text-xs font-dm px-2.5 py-1 rounded-full font-semibold"
                  style={{ background: 'rgba(0,212,170,0.2)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.35)' }}
                >
                  Eligible
                </span>
              </div>
            </div>
            <ul className="space-y-2">
              {ELIGIBLE_ITEMS.map(item => (
                <li key={item} className="flex items-center gap-2 text-sm font-dm" style={{ color: '#F0F4FF' }}>
                  <CheckCircle2 size={15} style={{ color: '#00D4AA', shrink: 0 }} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {result === 'not-eligible' && (
          <div
            className="rounded-2xl p-6 animate-fade-up"
            style={{ background: 'rgba(255,71,87,0.08)', border: '1px solid rgba(255,71,87,0.25)' }}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="animate-scale-in" style={{ color: '#FF4757' }}>
                <XCircle size={48} strokeWidth={1.5} />
              </div>
              <div>
                <h3 className="font-syne font-bold text-xl" style={{ color: '#F0F4FF' }}>Not Eligible at This Time</h3>
                <span
                  className="text-xs font-dm px-2.5 py-1 rounded-full font-semibold"
                  style={{ background: 'rgba(255,71,87,0.2)', color: '#FF4757', border: '1px solid rgba(255,71,87,0.35)' }}
                >
                  Not Eligible
                </span>
              </div>
            </div>
            <ul className="space-y-2 mb-4">
              {NOT_ELIGIBLE_REASONS.map(r => (
                <li key={r} className="flex items-start gap-2 text-sm font-dm" style={{ color: '#F0F4FF' }}>
                  <XCircle size={15} className="shrink-0 mt-0.5" style={{ color: '#FF4757' }} />
                  {r}
                </li>
              ))}
            </ul>
            <button
              className="font-dm font-bold text-sm px-5 py-2.5 rounded-xl transition-all hover:brightness-110"
              style={{ background: '#FF4757', color: '#fff' }}
            >
              Explore Alternative Plans
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
