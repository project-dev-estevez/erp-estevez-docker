/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { onMounted, useState, useRef, Component, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AttendanceRecognitionDialog extends Component {
    setup() {
        // Refs
        this.videoRef = useRef("video");
        this.imageRef = useRef("image");
        this.canvasRef = useRef("canvas");
        this.selectRef = useRef("select");

        // Services
        this.notificationService = useService("notification");

        // State
        this.state = useState({
            videoWidth: 0,
            videoHeight: 0,
            intervalId: null,
            matchedEmployeeId: null,
            matchCount: [],
            attendanceUpdated: false,
        });

        // Props
        this.faceapi = this.props.faceapi;
        this.descriptors = this.props.labeledFaceDescriptors;

        // Lifecycle
        onMounted(async () => {
            await this.initWebcam();
        });

        onWillUnmount(() => this.cleanUp());
    }

    // =======================
    // 🎥 Webcam initialization
    // =======================
    async initWebcam() {
        if (!navigator.mediaDevices) {
            this.showHttpsError();
            return;
        }

        try {
            const videoSelect = this.selectRef.el;
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.populateDeviceList(devices, videoSelect);

            videoSelect.onchange = () => this.startStream(videoSelect.value);
            await this.startStream(videoSelect.value);
        } catch (error) {
            console.error("Error inicializando webcam:", error);
            this.notify("No se pudo acceder a la cámara: " + error.message, "danger");
        }
    }

    async startStream(deviceId) {
        this.stopStream();

        const constraints = {
            video: deviceId ? { deviceId: { exact: deviceId } } : true,
        };

        try {
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            const video = this.videoRef.el;
            video.srcObject = stream;
            window.stream = stream;

            video.onloadedmetadata = async () => {
                await video.play();
                this.state.videoWidth = video.offsetWidth;
                this.state.videoHeight = video.offsetHeight;
                this.onVideoReady(video);
            };
        } catch (error) {
            this.notify("Error al iniciar la cámara: " + error.message, "danger");
        }
    }

    populateDeviceList(devices, selectElement) {
        const previousValue = selectElement.value;
        selectElement.innerHTML = "";

        devices
            .filter(d => d.kind === "videoinput")
            .forEach((device, index) => {
                const option = document.createElement("option");
                option.value = device.deviceId;
                option.text = device.label || `Cámara ${index + 1}`;
                selectElement.appendChild(option);
            });

        // Restaurar selección previa si aplica
        if ([...selectElement.options].some(opt => opt.value === previousValue)) {
            selectElement.value = previousValue;
        }
    }

    // =======================
    // 🤖 Face detection logic
    // =======================
    async onVideoReady(video) {
        const canvas = this.canvasRef.el;
        await this.waitForModelsToLoad();
        this.startFaceDetection(video, canvas);
    }

    async waitForModelsToLoad() {
        while (!this.isFaceDetectionModelLoaded() || this.descriptors.length === 0) {
            console.log("⏳ Esperando carga de modelos...");
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    startFaceDetection(video, canvas) {
        this.clearInterval();
        const displaySize = { width: this.state.videoWidth, height: this.state.videoHeight };
        this.faceapi.matchDimensions(canvas, displaySize);

        this.state.intervalId = setInterval(async () => {
            const ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const detections = await this.faceapi
                .detectSingleFace(video, this.getFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor();

            if (!detections) return;

            const resized = faceapi.resizeResults(detections, displaySize);
            faceapi.draw.drawDetections(canvas, resized);
            faceapi.draw.drawFaceLandmarks(canvas, resized);

            this.handleFaceMatch(resized, video, canvas);
        }, 200);
    }

    async handleFaceMatch(detection, video, canvas) {
        const maxDistance = 0.45;
        const matcher = new faceapi.FaceMatcher(this.descriptors, maxDistance);
        const result = matcher.findBestMatch(detection.descriptor);

        if (!result || result.label === "unknown" || result.distance >= 0.5) return;

        const [employeeId, label] = result.label.split(",");
        this.state.matchedEmployeeId = employeeId;

        if (label) {
            const box = detection.detection.box;
            new faceapi.draw.DrawBox(box, { label }).draw(canvas);
        }

        this.state.matchCount.push(result.label);

        if (
            this.state.matchedEmployeeId &&
            this.state.matchCount.length > 2 &&
            !this.state.attendanceUpdated
        ) {
            this.state.attendanceUpdated = true;
            this.clearInterval();
            await this.captureAndUpdateAttendance(video, detection, employeeId);
        }
    }

    async captureAndUpdateAttendance(video, detection, employeeId) {
        const { box } = detection.detection;
        const region = new faceapi.Rect(box.x - 100, box.y - 100, box.width + 200, box.height + 200);
        const [face] = await faceapi.extractFaces(video, [region]);
        if (!face) return;

        let faceBase64 = face.toDataURL("image/jpeg");
        faceBase64 = faceBase64.replace(/^data:image\/(png|jpg|jpeg);base64,/, "");
        this.updateAttendance(employeeId, faceBase64);
    }

    // =======================
    // 🧹 Utility methods
    // =======================
    clearInterval() {
        if (this.state.intervalId) clearInterval(this.state.intervalId);
    }

    stopStream() {
        if (window.stream) {
            window.stream.getTracks().forEach(track => track.stop());
        }
    }

    cleanUp() {
        this.clearInterval();
        this.stopStream();
    }

    notify(message, type = "info") {
        this.notificationService.add(message, { type });
    }

    showHttpsError() {
        this.notify(
            "Error HTTPS: La cámara web solo funciona con conexiones HTTPS. Tu instancia de Odoo debe estar configurada en modo HTTPS.",
            "danger"
        );
    }

    async updateAttendance(employeeId, image) {
        if (!employeeId || !image) return;
        this.props.updateRecognitionAttendance({ employee_id: employeeId, image });
        this.cleanUp();
        this.props.close();
    }

    // =======================
    // ⚙️ FaceAPI helpers
    // =======================
    getFaceDetectorOptions() {
        return new this.faceapi.TinyFaceDetectorOptions({ inputSize: 384, scoreThreshold: 0.5 });
    }

    getCurrentFaceDetectionNet() {
        return this.faceapi.nets.tinyFaceDetector;
    }

    isFaceDetectionModelLoaded() {
        return !!this.getCurrentFaceDetectionNet().params;
    }
}

AttendanceRecognitionDialog.components = { Dialog };
AttendanceRecognitionDialog.template = "attendance_face_recognition.AttendanceRecognitionDialog";
AttendanceRecognitionDialog.props = {
    faceapi: false,
    labeledFaceDescriptors: [],
    close: Function,
};
AttendanceRecognitionDialog.defaultProps = {};
