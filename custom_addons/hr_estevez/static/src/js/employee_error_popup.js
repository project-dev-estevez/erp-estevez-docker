/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { Dialog } from "@web/core/dialog/dialog";

patch(FormController.prototype, {
    setup() {
        // Llamamos el original
        super.setup(...arguments);

        const urlHash = window.location.hash;
        if (urlHash.includes("error=")) {
            const parts = urlHash.split("error=");
            const errorMsg = decodeURIComponent(parts[1] || "");

            if (errorMsg) {
                Dialog.alert(this, errorMsg, { title: "Error en documentos PDF" });

                // 🔥 Limpiar el hash para no repetir el popup
                const cleanHash = urlHash.split("&error=")[0];
                window.location.hash = cleanHash;
            }
        }
    },
});
