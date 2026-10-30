/** @odoo-module **/

import { useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { append, createElement, setAttributes } from "@web/core/utils/xml";
import { FormCompiler } from "@web/views/form/form_compiler";
import { FormRenderer } from "@web/views/form/form_renderer";

/**
 * 🔹 Chatter colapsable en todos los formularios
 *
 * El panel lateral (mensajes, actividades e historial) siempre nace oculto
 * y se muestra/oculta con un botón de flechas, igual que el panel de
 * búsqueda lateral (Empresa / Área).
 */

function createToggleButton() {
    const button = createElement("button");
    button.classList.add("o-estevez-chatter-toggle", "btn");
    setAttributes(button, {
        type: "button",
        "t-on-click": "() => __comp__.toggleEstevezChatter()",
        "t-att-title":
            "__comp__.estevezChatter.open ? 'Ocultar mensajes e historial' : 'Mostrar mensajes e historial'",
    });
    // Íconos para chatter lateral (« / ») y para chatter abajo (˅ / ˄); el CSS muestra el que aplica
    const sideIcon = createElement("i");
    sideIcon.classList.add("fa", "o-estevez-chatter-toggle-side");
    setAttributes(sideIcon, {
        "t-att-class":
            "__comp__.estevezChatter.open ? 'fa-angle-double-right' : 'fa-angle-double-left'",
    });
    const bottomIcon = createElement("i");
    bottomIcon.classList.add("fa", "o-estevez-chatter-toggle-bottom");
    setAttributes(bottomIcon, {
        "t-att-class":
            "__comp__.estevezChatter.open ? 'fa-angle-double-up' : 'fa-angle-double-down'",
    });
    const label = createElement("span");
    label.classList.add("o-estevez-chatter-toggle-label");
    setAttributes(label, {
        "t-esc": "__comp__.estevezChatter.open ? 'Ocultar mensajes e historial' : 'Mensajes e historial'",
    });
    append(button, [sideIcon, bottomIcon, label]);
    return button;
}

/**
 * 🔹 Parche FormCompiler
 */
patch(FormCompiler.prototype, {
    compile(node, params) {
        const res = super.compile(node, params);
        for (const chatterContainerHookXml of res.querySelectorAll(".o-mail-Form-chatter")) {
            if (chatterContainerHookXml.closest(".o_form_sheet")) {
                continue; // chatter dentro del sheet: se deja como está
            }
            const chatterContainerXml = chatterContainerHookXml.querySelector(
                "t[t-component='__comp__.mailComponents.Chatter']"
            );
            if (!chatterContainerXml) {
                continue;
            }
            // El chatter solo se monta al abrirlo (evita cargar mensajes mientras está oculto)
            setAttributes(chatterContainerXml, { "t-if": "__comp__.estevezChatter.open" });
            const currentClass = chatterContainerHookXml.getAttribute("t-attf-class") || "";
            setAttributes(chatterContainerHookXml, {
                "t-attf-class": `${currentClass} {{ __comp__.estevezChatter.open ? 'o-estevez-chatter-open' : 'o-estevez-chatter-collapsed' }}`,
            });
            chatterContainerHookXml.prepend(createToggleButton());
        }
        return res;
    },
});

/**
 * 🔹 Parche FormRenderer
 */
patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        // Siempre oculto, salvo que se llegue desde un enlace a un mensaje específico
        this.estevezChatter = useState({ open: Boolean(this.highlightMessageId) });
    },
    toggleEstevezChatter() {
        this.estevezChatter.open = !this.estevezChatter.open;
    },
});
