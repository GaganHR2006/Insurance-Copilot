import React, { createContext, useContext, useState } from 'react';

const UploadContext = createContext();

export function UploadProvider({ children }) {
    const [pdfUploaded, setPdfUploaded] = useState(false);
    const [policyFreebies, setPolicyFreebies] = useState([]);
    const [policyInsurer, setPolicyInsurer] = useState(null);

    const handleUploadSuccess = (apiResponse) => {
        const extracted = apiResponse?.extracted ?? {};
        const freebies = extracted?.freebies ?? [];

        if (apiResponse?.status === "success" || apiResponse?.status === "partial") {
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
