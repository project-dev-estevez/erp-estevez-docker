/** @odoo-module **/

import public_kiosk_app from "@hr_attendance/public_kiosk/public_kiosk_app";
const kioskAttendanceApp = public_kiosk_app.kioskAttendanceApp;

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService} from "@web/core/utils/hooks";
import { AttendanceRecognitionDialog } from "./attendance_recognition_dialog"
import { onWillStart, onMounted, useRef} from "@odoo/owl";
import { Deferred } from "@web/core/utils/concurrency";
import { rpc } from "@web/core/network/rpc";
import { loadCSS, loadJS , AssetsLoadingError} from '@web/core/assets';

patch(kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");

        // gelocation
        this.glocationContainerRef = useRef("glocation_container");
        this.glocationToggleRef = useRef("glocation_toggle");
        this.glocationViewRef = useRef("glocation_view");
        // geofence
        this.geofenceContainerRef = useRef("geofence_container");
        this.geofenceToggleRef = useRef("geofence_toggle");
        this.geofenceViewRef = useRef("geofence_view");
        // geoipaddress
        this.geoipaddressContainerRef = useRef("geoipaddress_container");
        this.geoipaddressToggleRef = useRef("geoipaddress_toggle");
        this.geoipaddressViewRef = useRef("geoipaddress_view");
        
        // session controls
        this.state.disabel_recognition = false;
        this.state.show_recognition = false;
        this.state.show_geolocation = false;
        this.state.show_geofence = false;
        this.state.show_ipaddress = false;

        //geolocation
        this.state.latitude = false;
        this.state.longitude = false;

        //geofence
        this.state.fence_ids = [];
        this.state.fence_is_inside = false;

        //ipaddress
        this.state.ipaddress = false;

        //recogniiton
        this.state.face_detected_employee = false;
        this.state.face_detected_photo = false;
        this.state.fece_is_main_init = false;

        //temp arrays
        this.labeledFaceDescriptors = [];

        onWillStart(async () => {   
            await this.loadResConfig();
            try {
                await loadJS('/hr_attendance_controls_adv/static/src/lib/faceapi/source/face-api.js');
                await loadCSS('/hr_attendance_controls_adv/static/src/lib/ol-6.12.0/ol.css');
                await loadCSS('/hr_attendance_controls_adv/static/src/lib/ol-ext/ol-ext.css');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-6.12.0/ol.js');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-ext/ol-ext.js');
            } catch (error) {
                if (!(error instanceof AssetsLoadingError)) {
                    throw error;
                }
            }
        });

        onMounted(async () => {
            await this.onMounted();
        });
    },
    async onMounted() {
        this.loadControls();
        this.state.show_check_inout_button = true;
    },
    async loadControls(){
        if (window.location.protocol == 'https:') {
            if (this.state.hr_attendance_geolocation_k) {
                this.state.show_geolocation = true;
                try {
                    await this._getGeolocation();
                }
                catch (error) {
                    console.error("Geolocation error:", error);
                }
            }
            if (this.state.hr_attendance_geofence_k) {
                this.state.show_geofence = true;
            }
            if (this.state.hr_attendance_face_recognition_k) {
                this.state.show_recognition = true;
                try {
                    await this._initRecognition();
                } catch (error) {
                    console.error("Facerecognitio failed:", error);
                }
            }
            if (this.state.hr_attendance_ip_k) {
                this.state.show_ipaddress = true;
                try {
                    await this._getIpAddress();
                } catch (error) {
                    console.error("IP Address retrieval failed:", error);
                }
            }
        }else{
            this.state.show_geolocation = false;
            this.state.show_geofence = false;
            this.state.show_ipaddress = false;
            this.state.show_recognition = false;
        }
        return true;
    },
    async loadResConfig(){
        const result = await rpc("/hr_attendance/attendance_res_config" ,{
            'token': this.props.token,
        });
        if (result){
            this.state.hr_attendance_geolocation_k = result.hr_attendance_geolocation_k ? result.hr_attendance_geolocation_k : false;
            this.state.hr_attendance_geofence_k = result.hr_attendance_geofence_k ? result.hr_attendance_geofence_k : false;
            this.state.hr_attendance_face_recognition_k = result.hr_attendance_face_recognition_k ? result.hr_attendance_face_recognition_k : false;
            this.state.hr_attendance_ip_k = result.hr_attendance_ip_k ? result.hr_attendance_ip_k : false;
        }
    },
    onToggleGeolocation(){
        var self = this;
        if (self.glocationToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.glocationViewRef.el.classList.remove('d-none');
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-down");
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-up");
        }
        else {
            self.glocationViewRef.el.classList.add('d-none');
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-down");
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-up")
        }
    },
    _getGeolocation() {
        return new Promise((resolve, reject) => {
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
    },
    async onTogglegeofence(){
        var self = this;        
        if (self.geofenceToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.geofenceViewRef.el.classList.remove('d-none');
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-up");
            if (self.state.olmap != undefined){
                self.state.olmap.setTarget(self.geofenceViewRef.el);
                setTimeout(function () {
                    self.state.olmap.updateSize()
                }, 400);
            }else{
                await this._getGeofenceMap();
            }
        }
        else {
            self.geofenceViewRef.el.classList.add('d-none');
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-up")
            if (self.state.olmap != undefined){
                self.state.olmap.setTarget(self.geofenceViewRef.el);
                setTimeout(function () {
                    self.state.olmap.updateSize()
                }, 400);
            }else{
                await this._getGeofenceMap();
            }
        }
    },
    _getGeofenceMap () {
        var self = this;
        return new Promise((resolve, reject) => {
            if (window.location.protocol == 'https:') {
                navigator.geolocation.getCurrentPosition(
                    async ({ coords: { accuracy, latitude, longitude } }) => {
                        if (latitude && longitude){
                            self.state = self.state || {}; // Ensure state is initialized
                            self.state.latitude = latitude;
                            self.state.longitude = longitude;

                            if (!self.state.olmap) {
                                var vectorSource = new ol.source.Vector({});
                                
                                self.state.olmap = await new ol.Map({
                                    layers: [
                                        new ol.layer.Tile({
                                            source: new ol.source.OSM(),
                                        }),
                                        new ol.layer.Vector({
                                            source: vectorSource
                                        })
                                    ],
            
                                    loadTilesWhileInteracting: true,
                                    view: new ol.View({
                                        center: [latitude, longitude],
                                        zoom: 2,
                                    }),
                                });
                                self.state.olmap.setTarget(self.geofenceViewRef.el);
                                const Coords = [longitude, latitude];
                                const Accuracy = ol.geom.Polygon.circular(Coords, accuracy);
                                vectorSource.clear(true);
                                vectorSource.addFeatures([
                                    new ol.Feature(Accuracy.transform('EPSG:4326', self.state.olmap.getView().getProjection())),
                                    new ol.Feature(new ol.geom.Point(ol.proj.fromLonLat(Coords)))
                                ]);
                                self.state.olmap.getView().fit(vectorSource.getExtent(), { duration: 100, maxZoom: 6 });
                                
                                setTimeout(function () {
                                    self.state.olmap.updateSize()
                                }, 400);
                            }
                            resolve(self.state.latitude, self.state.longitude);
                        }else {
                            reject("Geolocation data is missing.");
                        }
                    },
                    (error) => reject("Geolocation access denied.")
                );
            }else{
                resolve();
            }
        });
    },
    onToggleGeoipaddress(){
        var self = this;
        if (self.geoipaddressToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.geoipaddressViewRef.el.classList.remove('d-none');
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-up");
        }
        else {
            self.geoipaddressViewRef.el.classList.add('d-none');
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-up")
        }
    },
    _getIpAddress() {
        return new Promise(async (resolve, reject) => {
            if (window.location.protocol === 'https:') {
                await fetch("https://api.ipify.org?format=json")
                    .then(response => {
                        if (!response.ok) {
                            reject("Failed to fetch IP address.");
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.ip) {
                            this.state = this.state || {};
                            this.state.ipaddress = data.ip;
                            resolve(data.ip);
                        } else {
                            reject("IP address not found in response.");
                        }
                    })
                    .catch(error => {
                        console.error("Error fetching IP address:", error.message || error);
                        resolve();
                    });
            } else {
                resolve();
            }
        });
    },
    async _initRecognition(){
        var self = this;
        if (window.location.protocol == 'https:') {
            if (!("faceapi" in window)) {
                await self._loadFaceapi();
            } 
            else {
                await self._loadModels();
            }
        }
    },
    _loadFaceapi () {
        var self = this;
        if (!("faceapi" in window)) {
            (function (w, d, s, g, js, fjs) {
                g = w.faceapi || (w.faceapi = {});
                g.faceapi = { q: [], ready: function (cb) { this.q.push(cb); } };
                js = d.createElement(s); fjs = d.getElementsByTagName(s)[0];
                js.src = window.origin + '/hr_attendance_controls_adv/static/src/lib/faceapi/source/face-api.js';
                fjs.parentNode.insertBefore(js, fjs); js.onload = async function () {
                    console.log("apis loaded");
                    await self._loadModels();
                    self.def_face_recognition.resolve();
                };
            }(window, document, 'script'));
        }
    },
    async _loadModels() {
        var self = this;
        const promises = [];
        promises.push([
            faceapi.nets.tinyFaceDetector.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
            faceapi.nets.faceExpressionNet.loadFromUri('/hr_attendance_controls_adv/static/src/lib/faceapi/weights'),
        ])
        return Promise.all(promises).then(() => {
            self.loadLabeledImages();            
            return Promise.resolve();
        });
    },
    async loadLabeledImages(){
        var self = this;
        await rpc('/hr_attendance_controls_adv/loadLabeledImages/').then(async function (data) {            
            self.labeledFaceDescriptors = await Promise.all(
                data.map((data, i) => {  
                const descriptors = [];
                for (var i = 0; i < data.descriptors.length; i++) {                    
                    if (data.descriptors[i].length != 0) {
                        var desc = new Uint8Array([...window.atob(data.descriptors[i])].map(d => d.charCodeAt(0))).buffer;
                        if (desc.byteLength > 0){
                            descriptors.push(new Float32Array(desc));
                        }
                    }
                }
                return new faceapi.LabeledFaceDescriptors(data.label.toString(), descriptors);
            }));
        })
    },
    onClickRecongintion(){
        var self = this;
        if (self.state.show_recognition) {
            self.state.face_detected_employee = false;
            self.state.face_detected_photo = false;
            self.state.fece_is_main_init = true;
            self.dialog.add(AttendanceRecognitionDialog, {
                faceapi: faceapi,
                labeledFaceDescriptors : this.labeledFaceDescriptors,
                updateRecognitionAttendance: (rdata) => this.updateRecognitionAttendance(rdata),
            });
        }
    },
    async updateRecognitionAttendance( rdata ) {
        var self = this;
        var employeeId = parseInt(rdata.employee_id);
        
        self.state.face_detected_employee = rdata.employee_id;
        self.state.face_detected_photo = rdata.image;

        if (!employeeId){
            return self.notificationService.add(
                _t("Failed: Please try again. Employee not found."), 
                { type: "danger" }
            );
        }

        const employee = await rpc('attendance_employee_data',{
            'token': this.props.token,
            'employee_id': employeeId,
        })

        if (employee && employee.employee_name){
            if (employee.use_pin){
                self.employeeData = employee;
                self.switchDisplay('pin');
            }
            else{
                try {
                    await this.onManualFaceSelection(employeeId, false);
                }
                catch (error) {
                    return;
                }
            }
        }
    },
    async _validate_Geofence (employeeId) {
        var self = this;
        
        let fence_is_inside = false;
        let fence_ids = [];

        if (window.location.protocol == 'https:') {
            const records = await rpc('/hr_attendance/get_geofences/', {
                'token': self.props.token,
                'employee_id': parseInt(employeeId),
            });

            if (records && records.length > 0){
                const geolocation = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        ({ coords: { latitude, longitude } }) => resolve({ latitude, longitude }),
                        (err) => reject(err)
                    );
                });

                const coords = ol.proj.fromLonLat([geolocation.longitude, geolocation.latitude]);

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
                self.notificationService.add(_t("You haven't entered any of the geofence zones."), { type: "danger" });
            }
        }

        return {
            'fence_is_inside': fence_is_inside, 
            'fence_ids': fence_ids,
        };
    }, 
    async onManualSelection(employeeId, enteredPin) {
        if(this.state.show_geolocation || this.state.show_geofence || this.state.show_ipaddress || this.state.show_recognition){
            try {
                this.onManualFaceSelection(employeeId, enteredPin)
            }
            catch (error) {
                return;
            }
        }else{
            super.onManualSelection(employeeId, enteredPin);
        }
    },
    async onManualFaceSelection(employeeId, enteredPin){
        var self = this;
        if(self.state.show_geolocation || self.state.show_geofence || self.state.show_ipaddress || self.state.show_recognition){
            let c_latitude = self.state.latitude || 0.0000000;
            let c_longitude = self.state.longitude || 0.0000000;
            let c_fence_ids = Object.values(self.state.fence_ids) || [];
            let c_fence_is_inside = self.state.fence_is_inside || false;
            let c_ipaddress = self.state.ipaddress || false;
            let c_photo = self.state.face_detected_photo || false;
            var c_employee_id = self.state.face_detected_employee || false;
        

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
                    const { fence_is_inside, fence_ids } = await self._validate_Geofence(employeeId);
                    if (fence_is_inside && fence_ids.length > 0) {
                        c_fence_ids = Object.values(fence_ids);
                        c_fence_is_inside = fence_is_inside;
                        resolve(true);
                    } 
                    else {
                        reject("You haven't entered any of the geofence zones.");
                    }
                } catch (err) {
                    console.error(err);
                    reject(`Geofence validation error: ${err}`);
                }
                })
            : Promise.resolve(true);
            
            const faceRecognitionPromise = self.state.show_recognition
                ? (c_photo && c_employee_id
                    ? Promise.resolve(true)
                    : Promise.reject(new Error("Face recognition failed.")))
                : Promise.resolve(true);

            const ipAddressPromise = self.state.show_ipaddress
                ? (c_ipaddress
                    ? Promise.resolve(true)
                    : Promise.reject(new Error(_t("IP Address not loaded, Please try again."))))
                : Promise.resolve(true);
            
            
            const promises = [geolocationPromise, geofencePromise, ipAddressPromise, faceRecognitionPromise];
            try {
                const promidCheck = await Promise.all(promises);
                if (promidCheck.every(p => p)) {
                    const result = await rpc('manual_selection', {
                        'token': self.props.token,
                        'employee_id': employeeId,
                        'pin_code': enteredPin
                    });

                    if (result && result.attendance) {
                        self.state.disabel_recognition = true;
                        if (result.attendance.id && result.attendance_state === "checked_in") {
                            var checkIn = await rpc('/hr_attendance/update_checkin_controls', {
                                'token': self.props.token,
                                'attendance_id': parseInt(result.attendance.id),
                                'check_in_latitude': c_latitude,
                                'check_in_longitude': c_longitude,
                                'check_in_geofence_ids': c_fence_ids,
                                'check_in_photo': c_photo,
                                'check_in_ipaddress': c_ipaddress,
                            });

                            if (checkIn ) {
                                this.employeeData = result;
                                setTimeout(async () => {
                                    await this.switchDisplay('greet');
                                    self.state.disabel_recognition = false;
                                }, 2000);
                            }
                        }
                        
                        else if (result.attendance.id && result.attendance_state === "checked_out") {
                            var checkOut = await rpc('/hr_attendance/update_checkout_controls', {
                                'token': self.props.token,
                                'attendance_id': parseInt(result.attendance.id),
                                'check_out_latitude': c_latitude,
                                'check_out_longitude': c_longitude,
                                'check_out_geofence_ids': c_fence_ids,
                                'check_out_photo': c_photo,
                                'check_out_ipaddress': c_ipaddress,
                            });
                            if (checkOut) {
                                this.employeeData = result;
                                setTimeout(async () => {
                                    await this.switchDisplay('greet');
                                    self.state.disabel_recognition = false;
                                }, 2000);
                            }
                        }
                    } 
                    else {
                        if (enteredPin) {
                            this.displayNotification(_t("Wrong Pin"));
                        }
                    }

                    // Reset Recognition States
                    self.state.face_detected_photo = false;
                    self.state.face_detected_employee = false;
                    self.state.fece_is_main_init = false;
                }
            }
            catch (error) {
                console.error("Error during validation:", error);
                this.displayNotification(_t("Validation failed: " + error));
            }
        }
    },
});
