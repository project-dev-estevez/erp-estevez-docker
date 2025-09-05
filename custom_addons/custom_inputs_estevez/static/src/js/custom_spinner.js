/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import * as rpc from "@web/core/network/rpc";
import { router } from "@web/core/browser/router";
import { registry } from "@web/core/registry";

/**
 * Utilidades para mostrar/ocultar el spinner
 */
let spinnerStartTime = null;
const MIN_VISIBLE_TIME = 300; // ms

function showCustomSpinner() {
    if (!document.querySelector('.custom-global-spinner')) {
        const div = document.createElement("div");
        div.className = "custom-global-spinner";
        div.innerHTML = `<div class="loader"></div>`;
        document.body.appendChild(div);
        spinnerStartTime = Date.now();
    }
}

function hideCustomSpinner() {
    const spinner = document.querySelector('.custom-global-spinner');
    if (spinner) {
        const elapsed = Date.now() - spinnerStartTime;
        const remaining = MIN_VISIBLE_TIME - elapsed;
        setTimeout(() => spinner.remove(), remaining > 0 ? remaining : 0);
    }
}

/**
 * 🔹 Guardar referencias originales
 */
const originalRpc = rpc.rpc;
const originalPushState = router.pushState;
const originalReplaceState = router.replaceState;

/**
 * 🔹 Parche RPC
 */
patch(rpc, {
    async rpc(route, params, options) {
        try {
            showCustomSpinner();
            return await originalRpc.call(this, route, params, options);
        } finally {
            hideCustomSpinner();
        }
    },
});

/**
 * 🔹 Parche Router
 */
patch(router, {
    async pushState(state) {
        try {
            showCustomSpinner();
            return await originalPushState.call(this, state);
        } finally {
            hideCustomSpinner();
        }
    },

    async replaceState(state) {
        try {
            showCustomSpinner();
            return await originalReplaceState.call(this, state);
        } finally {
            hideCustomSpinner();
        }
    },
});

/**
 * 🔹 Parche Action Service (modo OWL)
 */
const actionRegistry = registry.category("services").get("action");
const originalStart = actionRegistry.start;

actionRegistry.start = (env, deps) => {
    const service = originalStart(env, deps);

    // Parchar el método doAction del service ya instanciado
    const originalDoAction = service.doAction;
    service.doAction = async (action, options) => {
        try {
            showCustomSpinner();
            return await originalDoAction(action, options);
        } finally {
            hideCustomSpinner();
        }
    };

    return service;
};

// Opcional
window.showCustomSpinner = showCustomSpinner;
window.hideCustomSpinner = hideCustomSpinner;
