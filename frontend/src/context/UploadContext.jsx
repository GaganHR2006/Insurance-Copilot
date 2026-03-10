import React, { createContext, useContext, useState, useEffect } from 'react';

const UploadContext = createContext(null);

// Use ONE consistent key everywhere
const STORAGE_KEY = "ic_policy";

export function UploadProvider({ children }) {
    const [policyData, setPolicyData] = useState(null);
    const [pdfUploaded, setPdfUploaded] = useState(false);
    const [policyFreebies, setPolicyFreebies] = useState([]);

    // Restore from localStorage on app start
    useEffect(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                setPolicyData(parsed);
                setPdfUploaded(true);
                if (parsed?.freebies) {
                    setPolicyFreebies(parsed.freebies);
                }
                console.log("[UploadContext] Restored from localStorage:",
                    parsed?.insurer,
                    "| treatments:", parsed?.covered_treatments?.length,
                    "| text chars:", parsed?.full_text?.length
                );
            }
        } catch (e) {
            console.error("[UploadContext] Restore failed:", e);
        }
    }, []);

    function storePolicy(data) {
        try {
            const src = data?.extracted ?? data ?? {};

            // Normalize — handle any shape the backend returns
            const policy = {
                insurer: src?.insurer ?? null,
                policy_name: src?.policy_name ?? null,
                covered_treatments: Array.isArray(src?.covered_treatments)
                    ? src.covered_treatments : [],
                exclusions: Array.isArray(src?.exclusions)
                    ? src.exclusions : [],
                waiting_period_days: src?.waiting_period_days ?? null,
                sum_insured: src?.sum_insured ?? null,
                room_rent_cap: src?.room_rent_cap ?? null,
                min_age: src?.min_age ?? 18,
                max_age: src?.max_age ?? 65,
                sub_limits: src?.sub_limits ?? {},
                network_hospitals: Array.isArray(src?.network_hospitals)
                    ? src.network_hospitals : [],
                freebies: Array.isArray(src?.freebies)
                    ? src.freebies : [],

                // Store full text for AI — limit to 4000 chars
                full_text: (data?.full_text ?? src?.full_text ?? "").slice(0, 4000),

                filename: data?.filename ?? "",
                uploaded_at: new Date().toISOString(),
            };

            localStorage.setItem(STORAGE_KEY, JSON.stringify(policy));
            setPolicyData(policy);
            setPdfUploaded(true);
            setPolicyFreebies(policy.freebies);

            console.log("[UploadContext] Stored policy:", {
                insurer: policy.insurer,
                treatments: policy.covered_treatments.length,
                exclusions: policy.exclusions.length,
                waiting: policy.waiting_period_days,
                textChars: policy.full_text.length,
                freebies: policy.freebies.length,
            });

            return policy;
        } catch (e) {
            console.error("[UploadContext] Store failed:", e);
            return null;
        }
    }

    function clearPolicy() {
        localStorage.removeItem(STORAGE_KEY);
        setPolicyData(null);
        setPdfUploaded(false);
        setPolicyFreebies([]);
    }

    // Build context object to send with every API call
    function getPolicyContext() {
        if (!policyData) return null;
        return {
            insurer: policyData.insurer,
            policy_name: policyData.policy_name,
            covered_treatments: policyData.covered_treatments ?? [],
            exclusions: policyData.exclusions ?? [],
            waiting_period_days: policyData.waiting_period_days,
            sum_insured: policyData.sum_insured,
            room_rent_cap: policyData.room_rent_cap,
            min_age: policyData.min_age ?? 18,
            max_age: policyData.max_age ?? 65,
            sub_limits: policyData.sub_limits ?? {},
            network_hospitals: policyData.network_hospitals ?? [],
            full_text: policyData.full_text ?? "",
        };
    }

    return (
        <UploadContext.Provider value={{
            policyData,
            pdfUploaded,
            storePolicy,
            clearPolicy,
            getPolicyContext,
            policyFreebies,
            setPolicyFreebies,
            policyInsurer: policyData?.insurer || null
        }}>
            {children}
        </UploadContext.Provider>
    );
}

export const useUpload = () => useContext(UploadContext);
