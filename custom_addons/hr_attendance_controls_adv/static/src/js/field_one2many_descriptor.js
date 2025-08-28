/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { X2ManyFieldDialog } from "@web/views/fields/relational_utils";
import { onWillStart } from '@odoo/owl';
import { AssetsLoadingError, loadJS } from '@web/core/assets';

patch(X2ManyFieldDialog.prototype, {
    setup() {
        super.setup();

        onWillStart(async () => {
            try {
                if (typeof faceapi === 'undefined') {
                    await Promise.all([
                        loadJS('/attendance_face_recognition/static/src/lib/source/face-api.js'),
                    ])
                }
            } catch (error) {
                if (!(error instanceof AssetsLoadingError)) {
                    throw error;
                }
            }
        });
    },

    load_models: function(){
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
            return Promise.resolve();
        });
    },

    async save({ saveAndNew }) {
        if(this.record.resModel === 'hr.employee.faces'){
            var self = this;
            var image = this.record.data.image || false;            
            if (image){
                var image = document.querySelector('#face_image div img');    
                self.getDescriptor(image);
            }
        }else{
            return super.save({ saveAndNew });
        }
    },

    async getDescriptor(image){
        var self = this;
        await self.load_models().then(async function(){
            var has_Detection_model = self.isFaceDetectionModelLoaded();
            var has_Recognition_model = self.isFaceRecognitionModelLoaded();
            var has_Landmark_model = self.isFaceLandmarkModelLoaded();            
            if (has_Detection_model && has_Recognition_model && has_Landmark_model){
                var img = document.createElement('img');
                img.src= image.src;
                // SsdMobilenetv1Options //Using tinyFaceDetector
                await await faceapi.detectSingleFace(img , new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks().withFaceDescriptor().then(function(result){
                    if (result != undefined && result && result.descriptor){
                        var descriptor = self.formatDescriptor(result.descriptor);
                        self.updateDescriptor(descriptor);
                    }else{

                    }
                });
            }else{
                return setTimeout(() => self.getDescriptor(image))
            }
        })
    },
    async updateDescriptor(descriptor){
        var self = this;
        this.record.update({
            'descriptor': descriptor
        });
        if (await this.record.checkValidity()) {
            const saved = (await this.props.save(this.record, {})) || this.record;
        } else {
            return false;
        }
        this.props.close();
        return true;
    },
    formatDescriptor(descriptor) {
        var self = this;
        let result = window.btoa(String.fromCharCode(...(new Uint8Array(descriptor.buffer))));
        return result;
    },
    getCurrentFaceDetectionNet() {
        var self = this;
        // ssdMobilenetv1 //Using tinyFaceDetector
        return faceapi.nets.tinyFaceDetector;
    },

    isFaceDetectionModelLoaded() {
        var self = this;
        return !!self.getCurrentFaceDetectionNet().params
    },

    getCurrentFaceRecognitionNet () {
        var self = this;
        return faceapi.nets.faceRecognitionNet;
    },

    isFaceRecognitionModelLoaded() {
        var self = this;
        return !!self.getCurrentFaceRecognitionNet().params
    },

    getCurrentFaceLandmarkNet() {
        var self = this;
        return faceapi.nets.faceLandmark68Net;
    },

    isFaceLandmarkModelLoaded() {
        var self = this;
        return !!self.getCurrentFaceLandmarkNet().params
    },
    
});