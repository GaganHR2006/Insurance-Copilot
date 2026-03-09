import React, { createContext, useContext, useState } from 'react';

const UploadContext = createContext();

export function UploadProvider({ children }) {
    const [pdfUploaded, setPdfUploaded] = useState(() => {
        return !!localStorage.getItem('insurance_pdf_data');
    });
    const [policyFreebies, setPolicyFreebies] = useState(() => {
        try {
            const data = localStorage.getItem('insurance_pdf_data');
            if (data) return JSON.parse(data)?.freebies || JSON.parse(data)?.extracted?.freebies || [];
        } catch { }
        return [];
    });
    const [policyInsurer, setPolicyInsurer] = useState(() => {
        try {
            const data = localStorage.getItem('insurance_pdf_data');
            if (data) return JSON.parse(data)?.insurer || JSON.parse(data)?.extracted?.insurer || null;
        } catch { }
        return null;
    });

    const handleUploadSuccess = (apiResponse) => {
        const extracted = apiResponse?.extracted ?? apiResponse ?? {};
        const freebies = extracted?.freebies ?? [];

        if (apiResponse?.status === "success" || apiResponse?.status === "partial" || apiResponse) {
            setPdfUploaded(true);
            setPolicyFreebies(freebies);
            setPolicyInsurer(extracted?.insurer ?? null);
        } else {
            setPdfUploaded(true);
            setPolicyFreebies([]);
        }
    };

    const resetUpload = () => {
        setPdfUploaded(false);
        setPolicyFreebies([]);
        setPolicyInsurer(null);
        localStorage.removeItem('insurance_pdf_data');
        localStorage.removeItem('insurance_policy_context');
    };

    return (
        <UploadContext.Provider value={{
            pdfUploaded, setPdfUploaded,
            policyFreebies, setPolicyFreebies,
            policyInsurer, setPolicyInsurer,
            handleUploadSuccess,
            resetUpload
        }}>
            {children}
        </UploadContext.Provider>
    );
}

export function useUpload() {
    return useContext(UploadContext);
}
