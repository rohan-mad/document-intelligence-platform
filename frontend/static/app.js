const processButton = document.getElementById("processButton");
const fileInput = document.getElementById("fileInput");
const documentType = document.getElementById("documentType");
const message = document.getElementById("message");


// -------------------------------------------------
// Process uploaded document
// -------------------------------------------------

async function processDocument() {

    const file = fileInput.files[0];

    if (!file) {
        message.textContent = "Please select a file.";
        return;
    }

    const formData = new FormData();

    formData.append("file", file);
    formData.append("document_type", documentType.value);

    processButton.disabled = true;
    processButton.textContent = "Processing...";
    message.textContent = "Processing document...";

    try {

        const response = await fetch(
            "/api/v1/documents/process",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail?.message ||
                "Document processing failed."
            );
        }

        message.textContent =
            "Document processed successfully.";

        showResult(data);

        await loadDocuments();

    } catch (error) {

        message.textContent = error.message;

    } finally {

        processButton.disabled = false;
        processButton.textContent = "Process Document";
    }
}


// -------------------------------------------------
// Load processed documents
// -------------------------------------------------

async function loadDocuments() {

    const table =
        document.getElementById("documentsTable");

    try {

        const response =
            await fetch("/api/v1/documents");

        const documents =
            await response.json();

        table.innerHTML = "";

        if (documents.length === 0) {

            table.innerHTML = `
                <tr>
                    <td colspan="4">
                        No documents processed yet.
                    </td>
                </tr>
            `;

            return;
        }

        documents.forEach(doc => {

            const row =
                document.createElement("tr");

            const documentLink =
                document.createElement("a");

            documentLink.href = "#";
            documentLink.textContent =
                doc.document_name;

            documentLink.onclick = function () {
                openDocument(
                    doc.ocument_name
                );
                return false;
            };

            const nameCell =
                document.createElement("td");

            nameCell.appendChild(documentLink);


            const typeCell =
                document.createElement("td");

            typeCell.textContent =
                doc.document_type;


            const statusCell =
                document.createElement("td");

            statusCell.textContent =
                doc.processing_status;

            statusCell.className =
                doc.processing_status === "PASS"
                    ? "pass"
                    : "failed";


            const timeCell =
                document.createElement("td");

            timeCell.textContent =
                doc.processed_at || "";


            row.appendChild(nameCell);
            row.appendChild(typeCell);
            row.appendChild(statusCell);
            row.appendChild(timeCell);

            table.appendChild(row);

        });

    } catch (error) {

        table.innerHTML = `
            <tr>
                <td colspan="4">
                    Failed to load documents.
                </td>
            </tr>
        `;
    }
}


// -------------------------------------------------
// Open saved document
// -------------------------------------------------

async function openDocument(documentName) {

    try {

        const response = await fetch(
            `/api/v1/documents/${encodeURIComponent(documentName)}`
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail?.message ||
                "Could not load document."
            );
        }

        showResult(data);

    } catch (error) {

        alert(error.message);
    }
}


// -------------------------------------------------
// Display result
// -------------------------------------------------

function showResult(data) {

    const resultSection =
        document.getElementById("resultSection");

    const resultContent =
        document.getElementById("resultContent");

    const rawJson =
        document.getElementById("rawJson");


    resultSection.classList.remove("hidden");


    const extracted =
        data.extracted_data || {};

    const validation =
        data.validation || {};


    let html = `

        <div class="result-grid">

            <div class="info-box">
                <strong>Document</strong><br>
                ${escapeHtml(data.document_name || "")}
            </div>

            <div class="info-box">
                <strong>Type</strong><br>
                ${escapeHtml(data.document_type || "")}
            </div>

            <div class="info-box">
                <strong>Status</strong><br>

                <span class="${
                    data.processing_status === "PASS"
                        ? "validation-pass"
                        : "validation-fail"
                }">

                    ${escapeHtml(
                        data.processing_status || ""
                    )}

                </span>
            </div>

            <div class="info-box">

                <strong>OCR Used</strong><br>

                ${escapeHtml(
                    String(
                        data.processing_metadata
                            ?.ocr_used ?? ""
                    )
                )}

            </div>

        </div>
    `;


    // ---------------------------------------------
    // Basic extracted information
    // ---------------------------------------------

    html += `
        <h3>Extracted Information</h3>
    `;


    if (extracted.document_title) {

        html += `
            <p>
                <strong>Title:</strong>
                ${escapeHtml(
                    extracted.document_title
                )}
            </p>
        `;
    }


    if (extracted.entity_name) {

        html += `
            <p>
                <strong>Entity:</strong>
                ${escapeHtml(
                    extracted.entity_name
                )}
            </p>
        `;
    }


    if (extracted.currency) {

        html += `
            <p>
                <strong>Currency:</strong>
                ${escapeHtml(
                    extracted.currency
                )}
            </p>
        `;
    }


    // ---------------------------------------------
    // Fields
    // ---------------------------------------------

    if (
        extracted.fields &&
        extracted.fields.length > 0
    ) {

        html += `
            <h3>Fields</h3>

            <div class="table-container">

                <table class="result-table">

                    <thead>

                        <tr>
                            <th>Field</th>
                            <th>Value</th>
                            <th>Page</th>
                            <th>Evidence</th>
                        </tr>

                    </thead>

                    <tbody>
        `;


        extracted.fields.forEach(field => {

            html += `
                <tr>

                    <td>
                        ${escapeHtml(
                            field.name || ""
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            field.value ?? "null"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            String(
                                field.page_number ?? ""
                            )
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            field.evidence ?? ""
                        )}
                    </td>

                </tr>
            `;

        });


        html += `
                    </tbody>

                </table>

            </div>
        `;
    }


    // ---------------------------------------------
    // Line items
    // ---------------------------------------------

    if (
        extracted.line_items &&
        extracted.line_items.length > 0
    ) {

        html += `
            <h3>Tables / Line Items</h3>

            <div class="table-container">

                <table class="result-table">

                    <thead>

                        <tr>
                            <th>Description</th>
                            <th>Values</th>
                            <th>Page</th>
                            <th>Evidence</th>
                        </tr>

                    </thead>

                    <tbody>
        `;


        extracted.line_items.forEach(item => {

            const values =
                (item.values || [])
                    .map(value =>
                        `${value.period}: ${value.value ?? "null"}`
                    )
                    .join("<br>");

            html += `
                <tr>

                    <td>
                        ${escapeHtml(
                            item.description || ""
                        )}
                    </td>

                    <td>
                        ${values}
                    </td>

                    <td>
                        ${escapeHtml(
                            String(
                                item.page_number ?? ""
                            )
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            item.evidence ?? ""
                        )}
                    </td>

                </tr>
            `;

        });


        html += `
                    </tbody>

                </table>

            </div>
        `;
    }


    // ---------------------------------------------
    // Validation
    // ---------------------------------------------

    const validationClass =
        validation.overall_status === "PASS"
            ? "validation-pass"
            : validation.overall_status === "FAIL"
                ? "validation-fail"
                : "validation-na";


    html += `

        <h3>Financial Validation</h3>

        <p>

            <strong>Overall Status:</strong>

            <span class="${validationClass}">

                ${escapeHtml(
                    validation.overall_status ||
                    "NOT_APPLICABLE"
                )}

            </span>

        </p>
    `;


    if (
        validation.checks &&
        validation.checks.length > 0
    ) {

        html += `
            <div class="table-container">

                <table class="result-table">

                    <thead>

                        <tr>
                            <th>Formula</th>
                            <th>Calculated</th>
                            <th>Reported</th>
                            <th>Variance</th>
                            <th>Status</th>
                        </tr>

                    </thead>

                    <tbody>
        `;


        validation.checks.forEach(check => {

            html += `
                <tr>

                    <td>
                        ${escapeHtml(
                            check.formula || ""
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            String(
                                check.calculated ?? ""
                            )
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            String(
                                check.reported ?? ""
                            )
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            String(
                                check.variance ?? ""
                            )
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            check.status || ""
                        )}
                    </td>

                </tr>
            `;

        });


        html += `
                    </tbody>

                </table>

            </div>
        `;
    }


    resultContent.innerHTML = html;


    // ---------------------------------------------
    // Raw JSON
    // ---------------------------------------------

    rawJson.textContent =
        JSON.stringify(data, null, 2);


    resultSection.scrollIntoView({
        behavior: "smooth"
    });
}


// -------------------------------------------------
// Prevent HTML injection
// -------------------------------------------------

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// -------------------------------------------------
// Load documents when page opens
// -------------------------------------------------

loadDocuments();