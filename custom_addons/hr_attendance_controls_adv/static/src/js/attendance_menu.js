/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";

import { useService } from "@web/core/utils/hooks";
import { onWillStart, useRef } from "@odoo/owl";
import { session } from "@web/session";
import { loadCSS, loadJS , AssetsLoadingError} from '@web/core/assets';
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
        
        // geofence
        this.geofenceContainerRef = useRef("geofence_container");
        this.geofenceToggleRef = useRef("geofence_toggle");
        this.geofenceViewRef = useRef("geofence_view");

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
        this.state.olmap = false;
        this.state.fence_is_inside = false;
        this.state.fence_ids = [];
        //ipaddress
        this.state.ipaddress = false;        

        //temp arrays
        this.labeledFaceDescriptors = [];

        //validate button
        this.state.show_check_inout_button = false;

        onWillStart(async () => {
            try {
                await loadJS('/hr_attendance_controls_adv/static/src/lib/faceapi/source/face-api.js');
                await loadCSS('/hr_attendance_controls_adv/static/src/lib/ol-6.12.0/ol.css');
                await loadCSS('/hr_attendance_controls_adv/static/src/lib/ol-ext/ol-ext.css');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-6.12.0/ol.js');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-ext/ol-ext.js');
                if (session.hr_attendance_geofence) {
                    await this.loadGeofences();
                }
            } catch (error) {
                if (!(error instanceof AssetsLoadingError)) {
                    throw error;
                }
            }
        });
    },

    async loadGeofences(){
        var self = this;
        const company_id = session.user_companies.allowed_companies[0] || session.user_companies.current_company || false;
        if (!company_id) {
            return;
        }
    
        const records = await self.orm.call('hr.attendance.geofence', "search_read", [
            [['company_id', '=', company_id], ['employee_ids', 'in', self.employee.id]],
            ['id', 'name', 'overlay_paths']
        ], {});

        if(records){
            self.state.geofences = records;
        }
    },

    async onOpenedContent(){
        this.loadControls();
        this.state.show_check_inout_button = true;
    },
    
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
        
        // 🎯 PASO 7A: Agregar attendance_status al estado para usar en templates
        this.state.attendance_status = this.employee.attendance_status;
        
        // 🎯 PASO 7B: Log para verificar
        console.log("✅ Employee data loaded, attendance_status:", this.employee.attendance_status);
    },

    async loadControls(){
        if (window.location.protocol == 'https:') {
            if (session.hr_attendance_geolocation) {
                this.state.show_geolocation = true;
                try {
                    await this._getGeolocation();
                }
                catch (error) {
                    console.log("Geolocation error:", error);
                }
            }
            if (session.hr_attendance_geofence) {
                this.state.show_geofence = true;
                try {
                    await this._getGeofenceMap();
                } catch (error) {
                    console.log("Geofence map error:", error);
                }
            }
            if (session.hr_attendance_ip) {
                this.state.show_ipaddress = true;
                try {
                    await this._getIpAddress();
                } catch (error) {
                    console.log("IP Address retrieval failed:", error);
                }
            }
            if (session.hr_attendance_face_recognition) {
                this.state.show_recognition = true;
                try {
                    await this._initRecognition();
                } catch (error) {
                    console.log("Facerecognitio failed:", error);
                }
            }
            if (session.hr_attendance_photo){
                this.state.show_photo = true;
            }
        }else{
            this.state.show_geolocation = false;
            this.state.show_geofence = false;
            this.state.show_ipaddress = false;
            this.state.show_recognition = false;
            this.state.show_photo = false;
        }

        return true;
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
        const toggleIcon = self.geofenceToggleRef.el;
        const viewElement = self.geofenceViewRef.el;
        
        if (toggleIcon.classList.contains('fa-angle-double-down')) {
            viewElement.classList.remove('d-none');
            toggleIcon.classList.replace('fa-angle-double-down', 'fa-angle-double-up');
            
            if (self.state.olmap) {
                self.state.olmap.setTarget(viewElement);
                setTimeout(() => {
                    self.state.olmap.updateSize();
                }, 400);
            } else {
                if (typeof ol !== 'undefined') {
                    await this._getGeofenceMap();
                }else{
                    console.log("OpenLayers is not loaded.");
                }
            }
        } else {
            viewElement.classList.add('d-none');
            toggleIcon.classList.replace('fa-angle-double-up', 'fa-angle-double-down');
            
            if (self.state.olmap) {
                self.state.olmap.setTarget(viewElement);
                setTimeout(() => {
                    self.state.olmap.updateSize();
                }, 400);
            } else {
                if (typeof ol !== 'undefined') {
                    await this._getGeofenceMap();
                }else{
                    console.log("OpenLayers is not loaded.");
                }
            }
        }        
    },

    _getGeofenceMap() {
        return new Promise((resolve, reject) => {
            if (window.location.protocol === 'https:') {
                navigator.geolocation.getCurrentPosition(
                    async ({ coords: { accuracy, latitude, longitude } }) => {
                        if (latitude && longitude) {
                            this.state = this.state || {}; // Ensure state is initialized
                            this.state.latitude = latitude;
                            this.state.longitude = longitude;
    
                            if (!this.state.olmap) {
                                const olmapDiv = this.geofenceViewRef?.el;
    
                                if (olmapDiv) {
                                    olmapDiv.style.width = "350px";
                                    olmapDiv.style.height = "200px";
                                }
    
                                const vectorSource = new ol.source.Vector({});
                                this.state.olmap = new ol.Map({
                                    layers: [
                                        new ol.layer.Tile({ source: new ol.source.OSM() }),
                                        new ol.layer.Vector({ source: vectorSource })
                                    ],
                                    loadTilesWhileInteracting: true,
                                    view: new ol.View({
                                        center: ol.proj.fromLonLat([longitude, latitude]),
                                        zoom: 2,
                                    }),
                                });
                                this.state.olmap.setTarget(olmapDiv);
                                
                                const Coords = [longitude, latitude];
                                const Accuracy = ol.geom.Polygon.circular(Coords, accuracy);
                                vectorSource.clear(true);
                                vectorSource.addFeatures([
                                    new ol.Feature(Accuracy.transform('EPSG:4326', this.state.olmap.getView().getProjection())),
                                    new ol.Feature(new ol.geom.Point(ol.proj.fromLonLat(Coords)))
                                ]);
                                this.state.olmap.getView().fit(vectorSource.getExtent(), { duration: 100, maxZoom: 6 });
                                
                                setTimeout(() => this.state.olmap.updateSize(), 400);
                            }
                            resolve();
                        } else {
                            reject("Geolocation data is missing.");
                        }
                    },
                    (error) => reject("Geolocation access denied.")
                );
            } else {
                resolve();
            }
        });
    },

    _getIpAddress() {
        return new Promise((resolve, reject) => {
            if (window.location.protocol === 'https:') {
                fetch("https://api.ipify.org?format=json")
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
                        console.log("Error fetching IP address:", error.message || error);
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
                self._loadFaceapi();
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
                js.src = window.origin + '/hr_attendance_controls_adv/static/src/lib/source/face-api.js';
                fjs.parentNode.insertBefore(js, fjs); js.onload = async function () {
                    console.log("apis loaded");
                    await self._loadModels();
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

    async _validate_Geofence () {
        var self = this;
        
        let fence_is_inside = false;
        let fence_ids = [];

        if (window.location.protocol == 'https:') {
            const company_id = session.user_companies.allowed_companies[0] || session.user_companies.current_company || false;            
            const records = await self.orm.call('hr.attendance.geofence', "search_read", [[['company_id', '=', company_id], ['employee_ids', 'in', self.employee.id]], ['id', 'name', 'overlay_paths']], {});
            
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
    
    async signInOut() {
        const self = this;
        console.log("Sign in out clicked");
        
        // 🚀 TEMPORALMENTE: Llamar al método padre para que funcione básicamente
        await super.signInOut();
        return;
    
    //     // Check if validation is required
    //     if (self.state.show_geolocation || self.state.show_geofence || self.state.show_ipaddress || self.state.show_recognition || self.state.show_photo || self.state.show_reason) {
    
    //         let c_latitude = self.state.latitude || 0.0000000;
    //         let c_longitude = self.state.longitude || 0.0000000;
    //         let c_fence_ids = [];
    //         let c_fence_is_inside = false;
    //         let c_ipaddress = self.state.ipaddress || false;
    //         let c_photo = false;
    //         let c_reason = '-';
            
    //         // Define Promises
    //         const geolocationPromise = self.state.show_geolocation
    //         ? (c_latitude && c_longitude
    //             ? Promise.resolve(true)
    //             : new Promise((resolve, reject) => {
    //                 navigator.geolocation.getCurrentPosition(
    //                     ({ coords: { latitude, longitude } }) => {
    //                         if (latitude && longitude) {
    //                             self.state.latitude = c_latitude = latitude;
    //                             self.state.longitude = c_longitude = longitude;
    //                             resolve({ latitude, longitude });
    //                         } else {
    //                             reject("Coordinates not found");
    //                         }
    //                     },
    //                     (error) => reject("Geolocation access denied")
    //                 );
    //             }))
    //         : Promise.resolve(true);
                    
    //         const geofencePromise = self.state.show_geofence
    //             ? new Promise(async (resolve, reject) => {
    //                 try {
    //                     const { fence_is_inside, fence_ids } = await self._validate_Geofence();
    //                     if (fence_is_inside && fence_ids.length > 0) {
    //                         c_fence_ids = Object.values(fence_ids);
    //                         c_fence_is_inside = fence_is_inside;
    //                         resolve(true);
    //                     } else {
    //                         reject("You haven't entered any of the geofence zones.");
    //                     }
    //                 } catch (err) {
    //                     console.log(err);
    //                     reject(`Geofence validation error: ${err}`);
    //                 }
    //               })
    //             : Promise.resolve(true);
    
    //         const ipAddressPromise = self.state.show_ipaddress
    //             ? (c_ipaddress
    //                   ? Promise.resolve(true)
    //                   : Promise.reject("IP Address not loaded, Please try again."))
    //             : Promise.resolve(true);
    
    //         const photoPromise = self.state.show_photo
    //             ? new Promise((resolve) => {
    //                   if (!c_photo) {
    //                       self.dialog.add(AttendanceWebcamDialog, {
    //                           uploadWebcamImage: (rdata) => {
    //                               if (rdata.image) {
    //                                   c_photo = rdata.image;
    //                                   resolve(true);
    //                               } else {
    //                                   reject("Photo not loaded, Please try again.");
    //                               }
    //                           }
    //                       });
    //                   } else {
    //                       resolve(true);
    //                   }
    //               })
    //             : Promise.resolve(true);
    
    //         const faceRecognitionPromise = self.state.show_recognition
    //             ? new Promise((resolve, reject) => {
    //                   if (self.labeledFaceDescriptors?.length) {
    //                       self.dialog.add(AttendanceRecognitionDialog, {
    //                           faceapi: faceapi,
    //                           labeledFaceDescriptors: self.labeledFaceDescriptors,
    //                           updateRecognitionAttendance: (rdata) => {
    //                               if (parseInt(self.employee.id) !== parseInt(rdata.employee_id)) {
    //                                   reject("The detected employee does not match the logged-in employee.");
    //                               } else {
    //                                   c_photo = rdata.image;
    //                                   resolve(true);
    //                               }
    //                           }
    //                       });
    //                   } else {
    //                       reject("Detection Failed: Resource not found. Please add it to your user's profile.");
    //                   }
    //               })
    //             : Promise.resolve(true);
    
    //         try {
    //             await Promise.all([geolocationPromise, geofencePromise, ipAddressPromise, photoPromise, faceRecognitionPromise]);
    //             if (!isIosApp()) {
    //                 navigator.geolocation.getCurrentPosition(
    //                     async ({coords: {latitude, longitude}}) => {
    //                         await rpc("/hr_attendance/systray_check_in_out", {
    //                             latitude,
    //                             longitude
    //                         }).then(async function(data){
    //                             if (data.attendance.id && data.attendance_state == "checked_in"){
    //                                 await rpc("/web/dataset/call_kw/hr.attendance/write", {
    //                                     model: "hr.attendance",
    //                                     method: "write",
    //                                     args: [parseInt(data.attendance.id), {
    //                                         'check_in_latitude': c_latitude || latitude,
    //                                         'check_in_longitude': c_longitude || longitude,
    //                                         'check_in_geofence_ids': c_fence_ids,
    //                                         'check_in_photo': c_photo,
    //                                         'check_in_ipaddress': c_ipaddress,
    //                                         'check_in_reason': c_reason,
    //                                     }],
    //                                     kwargs: {},
    //                                 });
    //                             }
    //                             else if(data.attendance.id && data.attendance_state == "checked_out"){
    //                                 await rpc("/web/dataset/call_kw/hr.attendance/write", {
    //                                     model: "hr.attendance",
    //                                     method: "write",
    //                                     args: [parseInt(data.attendance.id), {
    //                                         'check_out_latitude': c_latitude || latitude,
    //                                         'check_out_longitude': c_longitude || longitude,
    //                                         'check_out_geofence_ids': c_fence_ids,
    //                                         'check_out_photo': c_photo,
    //                                         'check_out_ipaddress': c_ipaddress,
    //                                         'check_out_reason': c_reason,
    //                                     }],
    //                                     kwargs: {},
    //                                 });
    //                             }
    //                         });
    //                         await this.searchReadEmployee()
    //                     },
    //                     async err => {
    //                         await rpc("/hr_attendance/systray_check_in_out")
    //                         .then(async function(data){
    //                             if (data.attendance.id && data.attendance_state == "checked_in"){
    //                                 await rpc("/web/dataset/call_kw/hr.attendance/write", {
    //                                     model: "hr.attendance",
    //                                     method: "write",
    //                                     args: [parseInt(data.attendance.id), {
    //                                         'check_in_latitude': c_latitude || false,
    //                                         'check_in_longitude': c_longitude || false,
    //                                         'check_in_geofence_ids': c_fence_ids,
    //                                         'check_in_photo': c_photo,
    //                                         'check_in_ipaddress': c_ipaddress,
    //                                         'check_in_reason': c_reason,
    //                                     }],
    //                                     kwargs: {},
    //                                 });
    //                             }
    //                             else if(data.attendance.id && data.attendance_state == "checked_out"){
    //                                 await rpc("/web/dataset/call_kw/hr.attendance/write", {
    //                                     model: "hr.attendance",
    //                                     method: "write",
    //                                     args: [parseInt(data.attendance.id), {
    //                                         'check_out_latitude': c_latitude || false,
    //                                         'check_out_longitude': c_longitude || false,
    //                                         'check_out_geofence_ids': c_fence_ids,
    //                                         'check_out_photo': c_photo,
    //                                         'check_out_ipaddress': c_ipaddress,
    //                                         'check_out_reason': c_reason,
    //                                     }],
    //                                     kwargs: {},
    //                                 });
    //                             }
    //                         });
    //                         await this.searchReadEmployee()
    //                     },
    //                     {
    //                         enableHighAccuracy: true,
    //                     }
    //                 )
    //             } else {
    //                 await rpc("/hr_attendance/systray_check_in_out")
    //                 await this.searchReadEmployee()
    //             }
    //         } catch (error) {
    //             console.log("Validation failed:", error);
    //             self.notificationService.add(_t(error), { type: "danger" });
    //         }
    //     }else{
    //         if (!isIosApp()) {
    //             navigator.geolocation.getCurrentPosition(
    //                 async ({coords: {latitude, longitude}}) => {
    //                     await rpc("/hr_attendance/systray_check_in_out", {
    //                         latitude,
    //                         longitude
    //                     })
    //                     await this.searchReadEmployee()
    //                 },
    //                 async err => {
    //                     await rpc("/hr_attendance/systray_check_in_out")
    //                     await this.searchReadEmployee()
    //                 },
    //                 {
    //                     enableHighAccuracy: true,
    //                 }
    //             )
    //         } else {
    //             await rpc("/hr_attendance/systray_check_in_out")
    //             await this.searchReadEmployee()
    //         }
    //     }
    }
});
export default ActivityMenu;
