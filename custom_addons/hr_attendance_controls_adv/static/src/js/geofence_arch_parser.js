/** @odoo-module */

import { unique } from "@web/core/utils/arrays";
import { visitXML } from "@web/core/utils/xml";
import { archParseBoolean } from "@web/views/utils";

export class GeofenceArchParser {
    parse(arch) {
        const archInfo = {
            fieldNames: [],
        };

        visitXML(arch, (node) => {
            switch (node.tagName) {
                case "geofence_view":
                    this.visitGanttView(node, archInfo);
                    break;
                case "field":
                    this.visitField(node, archInfo);
                    break;
            }
        });

        archInfo.fieldNames = unique(archInfo.fieldNames);
        return archInfo;
    }

    visitGanttView(node, archInfo) {
        if (node.hasAttribute("overlay_paths")) {
            archInfo.overlay_paths = node.getAttribute("overlay_paths");
        }
    }
    visitField(node, params) {
        params.fieldNames.push(node.getAttribute("name"));
    }
}
