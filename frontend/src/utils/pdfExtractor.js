// Browser-side PDF text extraction using PDF.js CDN
// No npm install needed — loads from CDN dynamically

let pdfjsLib = null

async function loadPdfJs() {
    if (pdfjsLib) return pdfjsLib

    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (window.pdfjsLib) {
            pdfjsLib = window.pdfjsLib
            pdfjsLib.GlobalWorkerOptions.workerSrc =
                "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js"
            return resolve(pdfjsLib)
        }

        const script = document.createElement("script")
        script.src =
            "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"
        script.onload = () => {
            pdfjsLib = window.pdfjsLib
            pdfjsLib.GlobalWorkerOptions.workerSrc =
                "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js"
            resolve(pdfjsLib)
        }
        script.onerror = () => reject(new Error("PDF.js failed to load"))
        document.head.appendChild(script)
    })
}


export async function extractTextFromPDF(
    file,
    maxPages = 8,
    maxChars = 4000
) {
    try {
        const lib = await loadPdfJs()

        // Read file as ArrayBuffer
        const arrayBuffer = await new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = e => resolve(e.target.result)
            reader.onerror = reject
            reader.readAsArrayBuffer(file)
        })

        // Load PDF document
        const pdf = await lib.getDocument({ data: arrayBuffer }).promise
        console.log(`[PDFExtract] Pages: ${pdf.numPages}`)

        let fullText = ""
        const pagesToRead = Math.min(pdf.numPages, maxPages)

        for (let i = 1; i <= pagesToRead; i++) {
            const page = await pdf.getPage(i)
            const content = await page.getTextContent()
            const pageText = content.items
                .map(item => item.str)
                .join(" ")
            fullText += pageText + "\n"

            if (fullText.length >= maxChars) break
        }

        const result = fullText.slice(0, maxChars).trim()
        console.log(`[PDFExtract] Extracted ${result.length} chars`)
        return result

    } catch (err) {
        console.error("[PDFExtract] Error:", err)
        return ""
    }
}
