import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, CheckCircle2, ShieldAlert } from 'lucide-react';
import { useUpload } from '../context/UploadContext';

export default function NotificationBell() {
    const [open, setOpen] = useState(false);
    const dropdownRef = useRef(null);
    const navigate = useNavigate();

    // Global context integration
    const { pdfUploaded, policyFreebies, setPolicyFreebies, policyInsurer } = useUpload();

    // Close when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleMarkUsed = async (id) => {
        try {
            const storedPdf = localStorage.getItem('insurance_pdf_data');
            let pdfPolicyData = storedPdf ? JSON.parse(storedPdf) : null;
            if (pdfPolicyData && pdfPolicyData.extracted) {
                pdfPolicyData = pdfPolicyData.extracted;
            }
            if (pdfPolicyData) {
                delete pdfPolicyData.full_text;
                delete pdfPolicyData.raw_text_snippet;
            }

            const resUsed = await fetch('/api/notifications/freebies/mark-used', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ freebie_id: id, used_count: 1, pdf_policy: pdfPolicyData })
            });

            if (resUsed.ok) {
                const usedData = await resUsed.json();
                if (usedData.updated_pdf_policy) {
                    localStorage.setItem('insurance_pdf_data', JSON.stringify(usedData.updated_pdf_policy));
                }
            }

            // Re-fetch strictly after user action to update available/used counters
            const newPdf = localStorage.getItem('insurance_pdf_data');
            let newPdfPolicyData = newPdf ? JSON.parse(newPdf) : null;
            if (newPdfPolicyData && newPdfPolicyData.extracted) {
                newPdfPolicyData = newPdfPolicyData.extracted;
            }
            if (newPdfPolicyData) {
                delete newPdfPolicyData.full_text;
                delete newPdfPolicyData.raw_text_snippet;
            }

            const res = await fetch('/api/notifications/freebies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pdf_policy: newPdfPolicyData })
            });

            if (res.ok) {
                const json = await res.json();
                setPolicyFreebies(json.freebies || []);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const activeCount = policyFreebies.filter(f => f.status !== "fully_used").length;

    const renderPanelContent = () => {
        // STATE 1: PDF not uploaded yet — show prompt only
        if (!pdfUploaded) {
            return (
                <div style={{ padding: "24px", textAlign: "center" }}>
                    <p style={{ fontSize: "32px", margin: 0 }}>📄</p>
                    <p style={{ color: "white", fontWeight: "bold", marginTop: "8px" }}>
                        No Policy Uploaded
                    </p>
                    <p style={{ color: "#64748b", fontSize: "13px", marginTop: "4px" }}>
                        Upload your insurance PDF to see your free benefits and track usage.
                    </p>
                    <button
                        onClick={() => {
                            setOpen(false);
                            navigate("/upload");
                        }}
                        style={{
                            marginTop: "16px",
                            background: "#00BFA5",
                            color: "white",
                            border: "none",
                            borderRadius: "8px",
                            padding: "8px 16px",
                            cursor: "pointer",
                            fontSize: "13px",
                            fontWeight: "500"
                        }}>
                        Upload Policy →
                    </button>
                </div>
            );
        }

        // STATE 2: PDF uploaded but no freebies found
        if (pdfUploaded && policyFreebies.length === 0) {
            return (
                <div style={{ padding: "24px", textAlign: "center" }}>
                    <p style={{ fontSize: "32px", margin: 0 }}>✅</p>
                    <p style={{ color: "white", fontWeight: "bold", marginTop: "8px" }}>
                        Policy Loaded
                    </p>
                    <p style={{ color: "#64748b", fontSize: "13px", marginTop: "4px" }}>
                        No trackable free benefits were detected in your policy document.
                    </p>
                </div>
            );
        }

        // STATE 3: PDF uploaded AND freebies found — show list
        const uniqueFreebies = policyFreebies.filter(
            (freebie, index, self) =>
                index === self.findIndex(f => f.id === freebie.id)
        );

        return (
            <div className="flex flex-col h-full">
                <div style={{ padding: "12px 16px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                    <p style={{ color: "white", fontWeight: "bold", fontSize: "14px" }}>
                        Policy Benefits & Freebies
                    </p>
                    <p style={{ color: "#00BFA5", fontSize: "11px", marginTop: "2px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                        ✓ Extracted from {policyInsurer ?? "your policy"}
                    </p>
                </div>

                <div style={{ padding: "8px", flex: 1, overflowY: "auto" }} className="space-y-1.5">
                    {uniqueFreebies.map(f => (
                        <div key={f.id} className="p-3 rounded-xl flex items-start justify-between gap-3 transition-colors"
                            style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <div className="flex gap-3">
                                <span className="text-2xl leading-none">{f.icon}</span>
                                <div>
                                    <p className="text-sm font-dm font-semibold" style={{ color: '#F0F4FF' }}>{f.label}</p>
                                    <p className="text-[10px] font-dm max-w-[180px] line-clamp-2 mt-0.5"
                                        style={{
                                            color: '#8892A4',
                                            display: '-webkit-box',
                                            WebkitLineClamp: 2,
                                            WebkitBoxOrient: 'vertical',
                                            overflow: 'hidden'
                                        }}
                                    >
                                        {(() => {
                                            const total = f.total_per_cycle;
                                            const value = f.value_inr;
                                            const month = f.renewal_month;
                                            const freq = f.frequency;

                                            let desc = "";
                                            if (total === 1) desc = "Once per policy year";
                                            else if (total > 1) desc = `Up to ${total} times per year`;
                                            else if (total === null) desc = "Covered as needed";

                                            if (value && value > 0) desc += ` · Up to ₹${value.toLocaleString('en-IN')}`;

                                            if (month) desc += ` · Renews in ${month}`;
                                            else if (freq === "yearly") desc += " · Renews with policy";
                                            else if (freq === "lifetime") desc += " · Lifetime benefit";
                                            else if (freq === "per_claim") desc += " · Available per claim";

                                            return desc || "Included in your policy";
                                        })()}
                                    </p>
                                    <div className="text-[10px] font-bold mt-1.5 uppercase tracking-wider" style={{ color: f.status === 'fully_used' ? '#FF4757' : '#00D4AA' }}>
                                        {f.status === 'fully_used' ? 'Fully Used' : f.total_per_cycle === null ? `Available (Used: ${f.used})` : `${f.remaining} / ${f.total_per_cycle} Remaining`}
                                    </div>
                                </div>
                            </div>
                            {f.status !== 'fully_used' && (
                                <button
                                    onClick={() => handleMarkUsed(f.id)}
                                    className="shrink-0 rounded-full px-2 py-1 text-[10px] font-bold font-dm transition-all hover:opacity-80 disabled:opacity-50"
                                    style={{ background: 'rgba(0,212,170,0.15)', color: '#00D4AA', cursor: 'pointer', border: 'none' }}
                                >
                                    Use 1
                                </button>
                            )}
                        </div>
                    ))}
                </div>

                <div style={{ padding: "10px", borderTop: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
                    <p style={{ fontSize: "11px", color: "#475569", margin: 0 }}>
                        Benefits reset annually with policy renewal
                    </p>
                </div>
            </div>
        );
    };

    return (
        <div style={{ position: "relative", display: "inline-block" }} ref={dropdownRef}>
            <button
                onClick={() => setOpen(!open)}
                className="relative p-2 rounded-xl transition-colors hover:bg-white/5"
                style={{ color: open ? '#F0F4FF' : '#8892A4', border: 'none', background: 'transparent', cursor: 'pointer' }}
                aria-label="Notifications"
            >
                <Bell size={20} />
                {pdfUploaded && activeCount > 0 && (
                    <span style={{
                        position: "absolute",
                        top: "-2px",
                        right: "-2px",
                        background: "#ef4444",
                        borderRadius: "50%",
                        width: "18px",
                        height: "18px",
                        fontSize: "10px",
                        color: "white",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontWeight: "bold",
                        border: "2px solid #0A0F1E"
                    }}>
                        {activeCount}
                    </span>
                )}
            </button>

            {open && (
                <>
                    {/* Backdrop Overlay */}
                    <div
                        className="fixed inset-0 z-[9998] bg-transparent"
                        onClick={() => setOpen(false)}
                    />

                    {/* Notification Dropdown Panel */}
                    <div
                        className="animate-fade-up flex flex-col"
                        style={{
                            position: "absolute",
                            top: "calc(100% + 8px)",
                            right: "0px",
                            width: "360px",
                            maxHeight: "480px",
                            overflowY: "auto",
                            zIndex: 9999,
                            backgroundColor: "#1a2235",
                            border: "1px solid rgba(255,255,255,0.1)",
                            borderRadius: "12px",
                            boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
                            // @media fallback:
                            ...(window.innerWidth <= 400 ? { right: '-16px', width: 'calc(100vw - 32px)' } : {})
                        }}
                    >
                        {renderPanelContent()}
                    </div>
                </>
            )}
        </div>
    );
}
