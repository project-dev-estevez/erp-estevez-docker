/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { GeofenceArchParser } from "./geofence_arch_parser";
import { GeofenceController } from "./geofence_controller";
import { GeofenceRenderer } from "./geofence_renderer";
import { GeofenceModel } from "./geofence_model";

export const GeofenceView = {
    type: "geofence_view",
    display_name: _t("Attendance Geofence"),
    icon: "fa fa-map-o",
    multiRecord: true,
    ArchParser: GeofenceArchParser,
    Controller: GeofenceController,
    Model: GeofenceModel,
    Renderer: GeofenceRenderer,
    searchMenuTypes: ["filter"],
    buttonTemplate: "hr_attendance_controls_adv.Buttons",
    props: (genericProps, view, config) => {
        let modelParams = genericProps.state;
        if (!modelParams) {
            const { arch,  resModel, fields, context} = genericProps;
            const parser = new view.ArchParser();
            const archInfo = parser.parse(arch);
            const views = config.views || [];
            modelParams = {
                context: context,
                fields: fields,
                fieldNames: archInfo.fieldNames,
                overlayPaths: archInfo.overlay_paths || false,
                hasFormView: views.some((view) => view[1] === "form"),
                resModel: resModel,
                defaultOrder: 'id',
            };
        }

        return {
            ...genericProps,
            Model: view.Model,
            modelParams,
            Renderer: view.Renderer,
            buttonTemplate: view.buttonTemplate,
        };
    }
};

registry.category('views').add('geofence_view', GeofenceView);
