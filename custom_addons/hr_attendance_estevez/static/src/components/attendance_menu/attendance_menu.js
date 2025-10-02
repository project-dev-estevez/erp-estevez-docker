/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.state.currentMoment = this.state.currentMoment || "unknown";
        this.state.buttonDisabled = false;
        console.log(
            "[Estevez] setup ejecutado → currentMoment inicial:",
            this.state.currentMoment
        );
    },

    async searchReadEmployee() {
        // PRIMERO obtener geolocalización y geocerca ANTES de llamar al padre
        console.log("[Estevez] searchReadEmployee iniciado - obteniendo geolocalización PRIMERO");
        if (window.location.protocol === 'https:' && !this.state.latitude) {
            await this._getGeolocation();
            console.log("[Estevez] Geolocalización completada antes de searchReadEmployee del padre:", this.state.latitude, this.state.longitude);
        }
        
        // Llamar siempre al original (esto ya carga geolocalización en hr_attendance_controls_adv)
        if (typeof super.searchReadEmployee === "function") {
            await super.searchReadEmployee();
        }
        console.log("[Estevez] searchReadEmployee completado → currentMoment:", this.state.currentMoment, "lat:", this.state.latitude, "lon:", this.state.longitude);
        
        // Verificar si ya existe un registro completo de asistencia hoy
        await this._checkTodayAttendance();
        
        // Actualizar momento (esto ya renderiza el mapa si es necesario)
        this._updateMoment();

        console.log(
            "[Estevez] searchReadEmployee completado →",
            this.state.currentMoment,
            this.state.geofence_name,
            this.state.geofence_description
        );
    },

    async signInOut() {
        if (this.state.buttonDisabled) return;
        this.state.buttonDisabled = true;
        this.render();
        try {
            if (typeof super.signInOut === "function") {
                await super.signInOut();
            }
            
            // Después de hacer check-in o check-out, verificar de nuevo la asistencia del día
            await this._checkTodayAttendance();
            this._updateMoment();
        } finally {
            setTimeout(() => {
                this.state.buttonDisabled = false;
                this.render();
            }, 5000);
        }
    },

    async _getGeolocation() {
        this.state.loading_geofence = true;
        let result;
        // Si existe método original, llamarlo
        if (typeof this._super === "function") {
            result = await this._super(...arguments);
        } else {
            // Lógica original si no existe _super
            result = await new Promise((resolve, reject) => {
                if (window.location.protocol === "https:") {
                    navigator.geolocation.getCurrentPosition(
                        ({ coords: { latitude, longitude } }) => {
                            if (latitude && longitude) {
                                this.state = this.state || {};
                                this.state.latitude = latitude;
                                this.state.longitude = longitude;
                                console.log(
                                    "[Estevez] Geolocalización obtenida:",
                                    latitude,
                                    longitude
                                );
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

    async _checkTodayAttendance() {
        // Obtener el employee_id desde this.employee (como lo hace el componente padre)
        const employee_id = this.employee?.id;
        if (!employee_id) {
            console.log("[Estevez] No se encontró employee_id, employee:", this.employee);
            this.state.hasCompletedAttendanceToday = false;
            return;
        }

        console.log("[Estevez] Verificando asistencia para employee_id:", employee_id);

        // Obtener fecha de hoy en formato YYYY-MM-DD
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        
        try {
            // Buscar registros de asistencia del empleado para hoy
            const attendances = await rpc(
                "/web/dataset/call_kw/hr.attendance/search_read",
                {
                    model: "hr.attendance",
                    method: "search_read",
                    args: [
                        [
                            ["employee_id", "=", employee_id],
                            ["check_in", ">=", todayStr + " 00:00:00"],
                            ["check_in", "<=", todayStr + " 23:59:59"],
                        ],
                        ["id", "check_in", "check_out"],
                    ],
                    kwargs: {},
                }
            );

            console.log("[Estevez] Registros de asistencia hoy:", attendances);

            // Verificar si existe al menos un registro completo (con check_in Y check_out)
            const hasCompleteAttendance = attendances.some(
                (att) => att.check_in && att.check_out
            );

            this.state.hasCompletedAttendanceToday = hasCompleteAttendance;
            
            console.log("[Estevez] ¿Tiene asistencia completa hoy?:", hasCompleteAttendance);
        } catch (error) {
            console.error("[Estevez] Error verificando asistencia del día:", error);
            this.state.hasCompletedAttendanceToday = false;
        }
    },

    async _findGeofenceByLocation() {
        // Usar el objeto global session para obtener company_id correctamente
        const company_id =
            session.user_companies?.current_company ||
            session.user_companies?.allowed_companies?.[0] ||
            false;
        if (!company_id) {
            this.state.geofence_name = false;
            this.state.geofence_description = false;
            console.log("[Estevez] No se encontró company_id para geocerca");
            return;
        }
        const geofences = await rpc(
            "/web/dataset/call_kw/hr.attendance.geofence/search_read",
            {
                model: "hr.attendance.geofence",
                method: "search_read",
                args: [
                    [["company_id", "=", company_id]],
                    ["id", "name", "description", "overlay_paths", "employee_ids"],
                ],
                kwargs: {},
            }
        );
        let found = false;
        if (
            window.ol &&
            geofences.length &&
            this.state.latitude &&
            this.state.longitude
        ) {
            const coords = window.ol.proj.fromLonLat([
                this.state.longitude,
                this.state.latitude,
            ]);
            for (const geofence of geofences) {
                try {
                    const value = JSON.parse(geofence.overlay_paths);
                    if (Object.keys(value).length > 0) {
                        const features = new window.ol.format.GeoJSON().readFeatures(
                            value
                        );
                        const geometry = features[0].getGeometry();
                        if (geometry.intersectsCoordinate(coords)) {
                            this.state.geofence_name = geofence.name;
                            this.state.geofence_description = geofence.description;
                            found = true;
                            console.log(
                                "[Estevez] Geocerca encontrada:",
                                geofence.name,
                                geofence.description
                            );
                            break;
                        }
                    }
                } catch (e) {
                    console.log(
                        "[Estevez] Error parseando overlay_paths de geocerca:",
                        e
                    );
                }
            }
        }
        if (!found) {
            this.state.geofence_name = false;
            this.state.geofence_description = false;
            console.log(
                "[Estevez] No se encontró geocerca para la ubicación actual"
            );
        }
    },

    _renderBeforeCheckinMap() {
        const mapDiv = document.getElementById("before-checkin-map");
        if (!mapDiv || !window.ol) {
            console.warn(
                "[Estevez] No se pudo inicializar el mapa (div u OL no disponibles)"
            );
            return;
        }

        // Limpiar si ya existe contenido
        mapDiv.innerHTML = "";

        const { latitude, longitude } = this.state;
        const coords = window.ol.proj.fromLonLat([longitude, latitude]);

        const vectorSource = new window.ol.source.Vector({
            features: [new window.ol.Feature(new window.ol.geom.Point(coords))],
        });

        const vectorLayer = new window.ol.layer.Vector({
            source: vectorSource,
        });

        const map = new window.ol.Map({
            target: mapDiv,
            layers: [
                new window.ol.layer.Tile({ source: new window.ol.source.OSM() }),
                vectorLayer,
            ],
            view: new window.ol.View({
                center: coords,
                zoom: 15,
            }),
        });

        console.log(
            "[Estevez] Mapa de ubicación inicial renderizado:",
            latitude,
            longitude
        );
    },

    _updateMoment() {
        // Lógica de momentos basada en estado actual y registro completo del día
        if (this.state.checkedIn) {
            // Empleado está actualmente en el trabajo (tiene check-in activo)
            this.state.currentMoment = "in_journey";
        } else if (!this.state.checkedIn && !this.state.hasCompletedAttendanceToday) {
            // Empleado NO está checked in Y NO tiene registro completo hoy
            this.state.currentMoment = "before_first_checkin";
        } else if (!this.state.checkedIn && this.state.hasCompletedAttendanceToday) {
            // Empleado NO está checked in pero YA completó su asistencia hoy
            this.state.currentMoment = "after_check_out";
        } else {
            this.state.currentMoment = "unknown";
        }

        console.log("state total: ", this.state);

        console.log("[Estevez] _updateMoment →", {
            checkedIn: this.state.checkedIn,
            hasCompletedAttendanceToday: this.state.hasCompletedAttendanceToday,
            currentMoment: this.state.currentMoment,
            hasCoordinates: !!(this.state.latitude && this.state.longitude)
        });
        
        // Renderizar mapa si estamos antes del primer checkin y tenemos coordenadas
        if (this.state.currentMoment === "before_first_checkin" && 
            this.state.latitude && 
            this.state.longitude) {
            console.log("[Estevez] Programando renderizado del mapa con coordenadas:", this.state.latitude, this.state.longitude);
            setTimeout(() => this._renderBeforeCheckinMap(), 100);
        }
    },
});

export default ActivityMenu;
