/** @odoo-module **/

import { useState } from "@odoo/owl";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { AppsBar } from "@muk_web_appsbar/webclient/appsbar/appsbar";

const LARGE = "mk_sidebar_type_large";
const SMALL = "mk_sidebar_type_small";

/**
 * 🔹 Parche AppsBar: botón para comprimir/expandir el menú lateral
 *
 * Cambia la clase del body al instante y guarda la preferencia del usuario
 * (res.users.sidebar_type), con la que el servidor pinta el body al recargar.
 */
patch(AppsBar.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.sidebarState = useState({
            compact: document.body.classList.contains(SMALL),
        });
    },
    async toggleSidebar() {
        const compact = !this.sidebarState.compact;
        this.sidebarState.compact = compact;
        document.body.classList.toggle(SMALL, compact);
        document.body.classList.toggle(LARGE, !compact);
        await this.orm.write("res.users", [user.userId], {
            sidebar_type: compact ? "small" : "large",
        });
    },
});
