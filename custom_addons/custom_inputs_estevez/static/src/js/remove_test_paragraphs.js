/** @odoo-module **/

function removeTestParagraphs(root = document) {
    const paragraphs = root.querySelectorAll("p.mb-0");
    paragraphs.forEach(p => {
        if (p.textContent.trim() === "Fue prueba") {
            p.remove();
        }
    });
}

function initRemoveTestParagraphs() {
    if (!document.body) {
        setTimeout(initRemoveTestParagraphs, 50);
        return;
    }

    // Eliminación inicial
    removeTestParagraphs();

    // Observador global para cambios dinámicos
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    removeTestParagraphs(node);
                }
            });
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
}

document.addEventListener("DOMContentLoaded", initRemoveTestParagraphs);
