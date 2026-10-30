/** @odoo-module **/

import { reactive, useState } from "@odoo/owl";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { AppsMenu } from "@muk_web_theme/webclient/appsmenu/appsmenu";

const { DateTime } = luxon;

// Compartido entre la barra (dibuja el contenido) y el menú (sabe cuándo se abre)
const homeState = reactive({ query: "" });

function normalize(text) {
    return (text || "")
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .toLowerCase()
        .trim();
}

/**
 * 🔹 Parche NavBar: saludo, fecha y filtro de aplicaciones
 */
patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.homeState = useState(homeState);
    },
    get homeGreeting() {
        const hour = DateTime.now().hour;
        const greeting = hour < 12 ? "Buenos días" : hour < 19 ? "Buenas tardes" : "Buenas noches";
        return `${greeting}, ${user.name.split(" ")[0]}`;
    },
    get homeDate() {
        const text = DateTime.now().setLocale(user.lang).toFormat("cccc d 'de' LLLL 'de' yyyy");
        return text.charAt(0).toUpperCase() + text.slice(1);
    },
    get homeApps() {
        const query = normalize(this.homeState.query);
        const apps = this.appMenuService.getAppsMenuItems();
        return query ? apps.filter((app) => normalize(app.name).includes(query)) : apps;
    },
    onHomeSearchKeydown(ev) {
        if (ev.key === "Escape") {
            return; // deja que el menú se cierre
        }
        // Evita que muk abra la paleta de comandos y que el menú navegue con las teclas
        ev.stopPropagation();
        if (ev.key === "Enter") {
            const [firstApp] = this.homeApps;
            if (firstApp) {
                this.onNavBarDropdownItemSelection(firstApp);
            }
        }
    },
});

/**
 * 🔹 Parche AppsMenu: buscador limpio y con el cursor listo al abrir
 */
patch(AppsMenu.prototype, {
    onOpened() {
        super.onOpened();
        homeState.query = "";
        this.menuRef.el?.querySelector(".o_estevez_home_search")?.focus();
    },
});
