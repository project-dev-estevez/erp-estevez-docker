/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";

import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { session } from "@web/session";
import { loadJS , AssetsLoadingError} from '@web/core/assets';
import { rpc } from "@web/core/network/rpc";

import { AttendanceRecognitionDialog } from "./attendance_recognition_dialog"
import { AttendanceWebcamDialog } from "./attendance_webcam_dialog"
import { isIosApp } from "@web/core/browser/feature_detection";

patch(ActivityMenu.prototype, {

    setup() {
        super.setup();
        this.orm = useService('orm');
        this.dialog = useService("dialog");
        this.notificationService = useService('notification');

        // session controls
        this.state.show_geolocation = false;
        this.state.show_geofence = false;
        this.state.show_ipaddress = false;
        this.state.show_recognition = false;
        this.state.show_photo = false;

        // gelocation
        this.state.latitude = false;
        this.state.longitude = false;
        // geofence
        this.state.fence_is_inside = false;
        this.state.fence_ids = [];
        this.state.geofences = [];  // Listado de geocercas asociadas al empleado
        //ipaddress
        this.state.ipaddress = false;        

        //temp arrays
        this.labeledFaceDescriptors = [];

        // Indican si el menú está listo para usarse y si está abierto
        this.state.isReady = false;
        this.state.show_check_inout_button = false;

        this.state.deviceInfo = {
            isMobile: false,
            platform: "Desconocido",
        };

        onWillStart(async () => {
            try {
                await loadJS('/hr_attendance_controls_adv/static/src/lib/faceapi/source/face-api.js');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-6.12.0/ol.js');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-ext/ol-ext.js');
                await this.searchReadEmployee();
                this.onOpenedContent();
            } catch (error) {
                if (!(error instanceof AssetsLoadingError)) {
                    throw error;
                }
            }
        });
    },

    // Carga los datos del empleado actual y actualiza el estado del menú
    async searchReadEmployee(){    
        const result = await rpc("/hr_attendance/attendance_user_data");
        this.employee = result;
        console.log("Employee data:", this.employee);

        if (!this.employee.id) {
            this.state.isDisplayed = false;
            return;
        }

        this.state.checkedIn = this.employee.attendance_state === "checked_in";
        this.isFirstAttendance = this.employee.hours_previously_today === 0;
        this.state.isDisplayed = this.employee.display_systray;
        this.state.attendance_status = this.employee.attendance_status;
        
        // 🎯 PASO 7B: Log para verificar
        console.log("✅ Employee data loaded, attendance_status:", this.employee.attendance_status);
    },

    async onOpenedContent() {
        if (this.state.isReady) {
            // Ya está todo listo, no recargar
            this.state.show_check_inout_button = true;
            return;
        }
        await this.loadControls();
        this.state.show_check_inout_button = true;
    },

    // Carga los controles configurados para el módulo de asistencia
    async loadControls(){
        if (window.location.protocol != 'https:'){
            this.state.show_geolocation = false;
            this.state.show_geofence = false;
            this.state.show_ipaddress = false;
            this.state.show_recognition = false;
            this.state.show_photo = false;

            return false;
        }

        this.loadDeviceInfo();

        // Obtener latitud y longitud del usuario
        if (session.hr_attendance_geolocation) {
            this.state.show_geolocation = true;
            try {
                await this._getGeolocation();
            }
            catch (error) {
                console.log("Geolocation error:", error);
            }
        }

        // Obtener geocercas associadas al empleado
        if (session.hr_attendance_geofence) {
            this.state.show_geofence = true;
            try {
                await this.loadGeofences();
            } catch (error) {
                console.log("Geofence map error:", error);
            }
        }

        // Obtener dirección IP del usuario
        if (session.hr_attendance_ip) {
            this.state.show_ipaddress = true;
            try {
                await this._getIpAddress();
            } catch (error) {
                console.log("IP Address retrieval failed:", error);
            }
        }

        // Inicializar reconocimiento facial
        if (session.hr_attendance_face_recognition) {
            this.state.show_recognition = true;
            try {
                await this._initRecognition();
            } catch (error) {
                console.log("Facerecognitio failed:", error);
            }
        }

        // Habilitar captura de foto
        if (session.hr_attendance_photo){
            this.state.show_photo = true;
        }

        this.state.isReady = true;
        return true;
    },

    // Carga la información del dispositivo desde el cual se está accediendo
    loadDeviceInfo() {
        const userAgentData = navigator.userAgentData;

        if (!userAgentData) return;

        const isMobile = userAgentData.mobile || false;
        const platform = userAgentData.platform || "Desconocido";

        this.state.deviceInfo = {
            isMobile,
            platform
        };
    },

    // Obtiene la geolocalización del usuario: Latitud y Longitud
    _getGeolocation() {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                async ({ coords: { latitude, longitude } }) => {
                    if (!(latitude && longitude)) {
                        return reject("Coordinates not found");                        
                    }

                    this.state.latitude = latitude;
                    this.state.longitude = longitude;
                    resolve({ latitude, longitude });
                },
                () => reject("Geolocation access denied")
            );
        });
    },

    // Obtiene las geocercas asociadas al empleado actual
    async loadGeofences(){
        const company_id = session.user_companies.allowed_companies[0] || session.user_companies.current_company || false;
        if (!company_id) {
            return;
        }

        const records = await this.orm.call('hr.attendance.geofence', "search_read", [
            [['company_id', '=', company_id], ['employee_ids', 'in', this.employee.id]],
            ['id', 'name', 'overlay_paths', 'description']
        ], {});

        // 🔒 ASEGURAR: Siempre mantener como array, incluso si records es null/undefined
        this.state.geofences = records || [];

        console.log("📍 Geofences loaded for employee ID", this.employee.id, ":", records);
        console.log("📊 Total geofences found:", this.state.geofences.length);
    },

    // Obtiene la dirección IP pública del usuario
    _getIpAddress() {
        return new Promise((resolve, reject) => {
            fetch("https://api.ipify.org?format=json")
                .then(response => {
                    if (!response.ok) {
                        return reject("Failed to fetch IP address.");
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data.ip) {
                        return reject("IP address not found in response.");
                    }
                    this.state.ipaddress = data.ip;
                    resolve(data.ip);
                })
                .catch(error => {
                    console.log("Error fetching IP address:", error.message || error);
                    resolve();
                });
        });
    },

    // Inicializa el reconocimiento facial cargando los modelos y descriptores
    async _initRecognition(){
        await this._loadModels();
    },

    // Carga los modelos de face-api.js y las imágenes etiquetadas del servidor
    async _loadModels() {
        const promises = [];
        promises.push([
            faceapi.nets.tinyFaceDetector.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceExpressionNet.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
        ])
        return Promise.all(promises).then(() => {
            this.loadLabeledImages();            
            return Promise.resolve();
        });
    },

    // Carga las imágenes etiquetadas del servidor y crea descriptores faciales
    async loadLabeledImages(){
        const self = this;
        await rpc('/hr_attendance_controls_adv/loadLabeledImages/').then(async function (data) {            
            self.labeledFaceDescriptors = await Promise.all(
                data.map((data, i) => {  
                const descriptors = [];
                for (let i = 0; i < data.descriptors.length; i++) {                    
                    if (data.descriptors[i].length != 0) {
                        let desc = new Uint8Array([...window.atob(data.descriptors[i])].map(d => d.charCodeAt(0))).buffer;
                        if (desc.byteLength > 0){
                            descriptors.push(new Float32Array(desc));
                        }
                    }
                }
                return new faceapi.LabeledFaceDescriptors(data.label.toString(), descriptors);
            }));
        })
    },
    
    async signInOut() {
        const self = this;
        
        // Cerrar dropdown de manera más robusta usando el parent
        try {
            self.dropdown.close();
        } catch (error) {
            console.warn('Error closing dropdown:', error);
        }

        // 🎯 Extraer la condición a una constante
        const hasValidationsEnabled = self.state.show_geolocation || 
                                    self.state.show_geofence || 
                                    self.state.show_ipaddress || 
                                    self.state.show_recognition || 
                                    self.state.show_photo || 
                                    self.state.show_reason;

        if (!hasValidationsEnabled) {
            console.log("No validations enabled, proceeding with default signInOut.");
            await super.signInOut();
            this.showNotification();            
            return; // ⚡ Early return
        }

        console.log("Validations enabled, proceeding with checks.");
    
        let c_latitude = self.state.latitude || 0.0000000;
        let c_longitude = self.state.longitude || 0.0000000;
        let c_fence_ids = [];
        let c_fence_is_inside = false;
        let c_ipaddress = self.state.ipaddress || false;
        let c_photo = false;
        let c_reason = '-';

        // 📱 Agregar variables para device info
        let c_is_mobile = self.state.deviceInfo?.isMobile || false;
        let c_device = self.state.deviceInfo?.platform || 'Unknown';
        
        // Define Promises
        const geolocationPromise = self.state.show_geolocation
        ? (c_latitude && c_longitude
            ? Promise.resolve(true)
            : new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    ({ coords: { latitude, longitude } }) => {
                        if (latitude && longitude) {
                            self.state.latitude = c_latitude = latitude;
                            self.state.longitude = c_longitude = longitude;
                            resolve({ latitude, longitude });
                        } else {
                            reject("Coordinates not found");
                        }
                    },
                    (error) => reject("Geolocation access denied")
                );
            }))
        : Promise.resolve(true);
                
        const geofencePromise = self.state.show_geofence
            ? new Promise(async (resolve, reject) => {
                try {
                    const { fence_is_inside, fence_ids } = await self._validate_Geofence();
                    if (fence_is_inside && fence_ids.length > 0) {
                        c_fence_ids = Object.values(fence_ids);
                        c_fence_is_inside = fence_is_inside;
                        resolve(true);
                    } else {
                        reject("You haven't entered any of the geofence zones.");
                    }
                } catch (err) {
                    console.log(err);
                    reject(`Geofence validation error: ${err}`);
                }
                })
            : Promise.resolve(true);

        const ipAddressPromise = self.state.show_ipaddress
            ? (c_ipaddress
                    ? Promise.resolve(true)
                    : Promise.reject("IP Address not loaded, Please try again."))
            : Promise.resolve(true);

        const photoPromise = self.state.show_photo
            ? new Promise((resolve) => {
                    if (!c_photo) {
                        self.dialog.add(AttendanceWebcamDialog, {
                            uploadWebcamImage: (rdata) => {
                                if (rdata.image) {
                                    c_photo = rdata.image;
                                    resolve(true);
                                } else {
                                    reject("Photo not loaded, Please try again.");
                                }
                            }
                        });
                    } else {
                        resolve(true);
                    }
                })
            : Promise.resolve(true);

        const faceRecognitionPromise = self.state.show_recognition
            ? new Promise(async (resolve, reject) => {
                    try {
                        // 🔄 VERIFICAR Y CARGAR: Si no hay descriptores, cargarlos
                        if (!self.labeledFaceDescriptors?.length) {
                            console.log("⚡ Face descriptors not loaded, loading them now...");
                            await self._initRecognition(); // Cargar modelos y descriptores
                            
                            // 🔍 VERIFICAR NUEVAMENTE: Después de cargar
                            if (!self.labeledFaceDescriptors?.length) {
                                reject("Detection Failed: No face images found in user profile. Please add a photo to your profile.");
                                return;
                            }
                            console.log("✅ Face descriptors loaded successfully!");
                        }
                        
                        // ✅ PROCEDER: Con reconocimiento facial
                        self.dialog.add(AttendanceRecognitionDialog, {
                            faceapi: faceapi,
                            labeledFaceDescriptors: self.labeledFaceDescriptors,
                            currentEmployeeId: self.employee.id.toString(), // 🔐 Pasar ID del empleado logueado
                            updateRecognitionAttendance: (rdata) => {
                                if (parseInt(self.employee.id) !== parseInt(rdata.employee_id)) {
                                    reject("El empleado reconocido no coincide con el usuario actual.");
                                } else {
                                    this.showNotification();
                                    c_photo = rdata.image;
                                    resolve(true);
                                }
                            }
                        });
                    } catch (error) {
                        console.error("❌ Face recognition error:", error);
                        reject(`Face recognition failed: ${error.message || error}`);
                    }
                })
            : Promise.resolve(true);

        try {
            console.log("Starting validation checks...");
            await Promise.all([geolocationPromise, geofencePromise, ipAddressPromise, photoPromise, faceRecognitionPromise]);
            if (isIosApp()) {
                console.log("iOS App detected, proceeding with signInOut without geolocation.");
                await rpc("/hr_attendance/systray_check_in_out");
                await this.searchReadEmployee();
            }
            
            console.log("Proceeding with signInOut after validations.");
            await rpc("/hr_attendance/systray_check_in_out", {
                latitude,
                longitude
            }).then(async function(data){

                if ( !data.attendance.id ) {
                    return self.notificationService.add("No se encontró el registro de asistencia.", { type: "danger" });
                }

                let inOrOut = '';
                if (data.attendance_state == "checked_in") {
                    inOrOut = 'in';
                } else if (data.attendance_state == "checked_out") {
                    inOrOut = 'out';
                }

                // Construir el objeto de campos dinámicamente según inOrOut
                const attendanceFields = {
                    [`check_${inOrOut}_latitude`]: c_latitude,
                    [`check_${inOrOut}_longitude`]: c_longitude,
                    [`check_${inOrOut}_geofence_ids`]: c_fence_ids,
                    [`check_${inOrOut}_photo`]: c_photo,
                    [`check_${inOrOut}_ipaddress`]: c_ipaddress,
                    [`check_${inOrOut}_reason`]: c_reason,
                    [`is_check${inOrOut}_mobile`]: c_is_mobile,
                    [`check${inOrOut}device`]: c_device,
                };

                await rpc("/web/dataset/call_kw/hr.attendance/write", {
                    model: "hr.attendance",
                    method: "write",
                    args: [parseInt(data.attendance.id), attendanceFields],
                    kwargs: {},
                });
            });
            await this.searchReadEmployee();

        } catch (error) {
            console.log("Validation failed:", error);
            self.notificationService.add(error, { type: "danger" });
        }
    },

    async _validate_Geofence() {
        var self = this;
        
        let fence_is_inside = false;
        let fence_ids = [];

        const company_id = session.user_companies.allowed_companies[0] || session.user_companies.current_company || false;            
        const records = await self.orm.call('hr.attendance.geofence', "search_read", [[['company_id', '=', company_id], ['employee_ids', 'in', self.employee.id]], ['id', 'name', 'overlay_paths']], {});
        
        console.log("1.Geofence records fetched:", records);

        if (records && records.length > 0){
            console.log("2.Validating geofence for coordinates:", self.state.latitude, self.state.longitude);

            const coords = ol.proj.fromLonLat([self.state.longitude, self.state.latitude]);

            for (const record of records) {
                const value = JSON.parse(record.overlay_paths);
                if (Object.keys(value).length > 0) {
                    const features = new ol.format.GeoJSON().readFeatures(value);
                    const geometry = features[0].getGeometry();
                    
                    if (geometry.intersectsCoordinate(coords)) {
                        fence_is_inside = true;
                        fence_ids.push(parseInt(record.id));
                    }
                }
            }
        }
        else{
            console.log("3.No geofence records found for employee ID:", self.employee.id);
            self.notificationService.add("You haven't entered any of the geofence zones.", { type: "danger" });
        }

        return {
            'fence_is_inside': fence_is_inside, 
            'fence_ids': fence_ids,
        };
    },

    showNotification() {
        this.notificationService.add(
            "Gracias por tu contribución. 🎉",
            { 
                type: "success",
                title: "¡Excelente!",
                sticky: false
            }
        );
    },
});
export default ActivityMenu;
