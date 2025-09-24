/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";

patch(ActivityMenu.prototype, {
    async _getGeolocation() {
        this.state.loading_geofence = true;
        let result;
        if (typeof this._super === "function") {
            result = await this._super(...arguments);
        } else {
            // Lógica original si no existe _super
            result = await new Promise((resolve, reject) => {
                if (window.location.protocol === 'https:') {
                    navigator.geolocation.getCurrentPosition(
                        ({ coords: { latitude, longitude } }) => {
                            if (latitude && longitude) {
                                this.state = this.state || {};
                                this.state.latitude = latitude;
                                this.state.longitude = longitude;
                                resolve({ latitude, longitude });
                            } else {
                                reject("Coordinates not found");
                            }
                        },
                        (error) => reject("Geolocation access denied")
                    );
                } else {
                    resolve();
                }
            });
        }
        if (this.state.latitude && this.state.longitude) {
            await this._findGeofenceByLocation();
        }
        this.state.loading_geofence = false;
        return result;
    },
    async _findGeofenceByLocation() {
    // Usar el objeto global session para obtener company_id correctamente
    const company_id = session.user_companies?.current_company || session.user_companies?.allowed_companies?.[0] || false;
        if (!company_id) {
            this.state.geofence_name = false;
            this.state.geofence_description = false;
            return;
        }
        const geofences = await rpc('/web/dataset/call_kw/hr.attendance.geofence/search_read', {
            model: 'hr.attendance.geofence',
            method: 'search_read',
            args: [[['company_id', '=', company_id]], ['id', 'name', 'description', 'overlay_paths', 'employee_ids']],
            kwargs: {},
        });
        let found = false;
        if (window.ol && geofences.length && this.state.latitude && this.state.longitude) {
            const coords = window.ol.proj.fromLonLat([this.state.longitude, this.state.latitude]);
            for (const geofence of geofences) {
                try {
                    const value = JSON.parse(geofence.overlay_paths);
                    if (Object.keys(value).length > 0) {
                        const features = new window.ol.format.GeoJSON().readFeatures(value);
                        const geometry = features[0].getGeometry();
                        if (geometry.intersectsCoordinate(coords)) {
                            this.state.geofence_name = geofence.name;
                            this.state.geofence_description = geofence.description;
                            found = true;
                            break;
                        }
                    }
                } catch (e) {
                    // Silenciar errores de parseo
                }
            }
        }
        if (!found) {
            this.state.geofence_name = false;
            this.state.geofence_description = false;
        }
    }
});
