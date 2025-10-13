/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { onMounted, useState, useRef, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { FACE_DETECTION_CONFIG, FACE_DETECTION_MESSAGES } from "./attendance_recognition_config";

export class AttendanceRecognitionDialog extends Component {

    setup() {

      this.notificationService = useService('notification');

      this.videoRef = useRef("video");
      this.imageRef = useRef("image");
      this.canvasRef = useRef("canvas");
      this.selectRef = useRef("select");
      this.progressRef = useRef("progress");

      this.state = useState({
        videoElwidth: 0,
        videoElheight: 0,
        intervalID: false,
        match_employee_id : false,
        match_count : [],
        attendanceUpdated: false,
        smileTime: 0,
        smiling: false,
        progressPercent: 0,
        smilePhaseCompleted: false,
      });

      this.faceapi = this.props.faceapi;
      this.descriptors = this.props.labeledFaceDescriptors;

      onMounted(async () => {
          await this.loadWebcam();            
      });  
    }

    loadWebcam(){
      var self = this;

      if (!navigator.mediaDevices) {
        this.notificationService.add( FACE_DETECTION_MESSAGES.HTTPS_WARNING, { type: "danger" } );
        return;
      }

      var videoElement = this.videoRef.el;
      var imageElement = this.imageRef.el;
      var videoSelect =this.selectRef.el;
      const selectors = [videoSelect];

      startStream();
      videoSelect.onchange = startStream;
      navigator.mediaDevices.enumerateDevices().then(gotDevices).catch(handleError);

      function startStream() {
          if (window.stream) {
            window.stream.getTracks().forEach(track => track.stop());
          }
          const videoSource = videoSelect.value;
          const constraints = {
            video: {deviceId: videoSource ? {exact: videoSource} : undefined}
          };
          navigator.mediaDevices.getUserMedia(constraints)
            .then(gotStream)
            .then(gotDevices)
            .catch(handleError);
      }

      function gotStream(stream) {
          window.stream = stream;
          videoElement.srcObject = stream;
          videoElement.onloadedmetadata = function(e) {
              videoElement.play().then(function(){
                self.onLoadStream();
              });
              self.state.videoEl = videoElement;
              self.state.imageEl = imageElement;
              self.state.videoElwidth = videoElement.offsetWidth;
              self.state.videoElheight = videoElement.offsetHeight;
          };
          return navigator.mediaDevices.enumerateDevices();
      }

      function gotDevices(deviceInfos) {
          const values = selectors.map(select => select.value);
          selectors.forEach(select => {
            while (select.firstChild) select.removeChild(select.firstChild);
          });
          for (let i = 0; i !== deviceInfos.length; ++i) {
            const deviceInfo = deviceInfos[i];
            const option = document.createElement('option');
            option.value = deviceInfo.deviceId;
            if (deviceInfo.kind === 'videoinput') {
              option.text = deviceInfo.label || `camera ${videoSelect.length + 1}`;
              videoSelect.appendChild(option);
            }
          }
          selectors.forEach((select, selectorIndex) => {
            if (Array.prototype.slice.call(select.childNodes).some(n => n.value === values[selectorIndex])) {
              select.value = values[selectorIndex];
            }
          });
      }
      
      function handleError(error) {
          console.log('navigator.MediaDevices.getUserMedia error: ', error.message, error.name);
      } 

    }

    onLoadStream(){
      var self = this;
      if (self.state.intervalID) clearInterval(self.state.intervalID);
      var video = self.state.videoEl;
      var canvas = self.canvasRef.el;
      self.detectSmile(video, canvas);        
    }

    async detectSmile(video, canvas) {
      var self = this;
      if (!video || !this.isFaceDetectionModelLoaded()) return;

      var displaySize = { 
        width : self.state.videoElwidth,
        height : self.state.videoElheight,
      };
      self.faceapi.matchDimensions(canvas, displaySize);

      self.state.intervalID = setInterval(async () => {
          const detections = await self.faceapi
            .detectSingleFace(video, new self.faceapi.TinyFaceDetectorOptions())
            .withFaceExpressions();

          if (detections && detections.expressions) {
              const happyScore = detections.expressions.happy || 0;
              if (happyScore > FACE_DETECTION_CONFIG.SMILE.HAPPINESS_THRESHOLD) {
                  self.state.smiling = true;
                  self.state.smileTime += FACE_DETECTION_CONFIG.SMILE.TIME_INCREMENT; // cada 200ms
              } else {
                  self.state.smiling = false;
                  self.state.smileTime = 0;
              }

              self.state.progressPercent = Math.min(
                (self.state.smileTime / FACE_DETECTION_CONFIG.SMILE.REQUIRED_DURATION) * 100, 
                100
              );
              if (self.progressRef.el)
                self.progressRef.el.style.width = `${self.state.progressPercent}%`;

              if (self.state.smileTime >= FACE_DETECTION_CONFIG.SMILE.REQUIRED_DURATION && !self.state.smilePhaseCompleted) {
                  self.state.smilePhaseCompleted = true;
                  clearInterval(self.state.intervalID);
                  self.notificationService.add( FACE_DETECTION_MESSAGES.SMILE_SUCCESS, {type: "success"} );
                  setTimeout(() => self.FaceDetector(video, canvas), FACE_DETECTION_CONFIG.UI.SMILE_COMPLETION_DELAY);
              }
          }
      }, FACE_DETECTION_CONFIG.SMILE.DETECTION_INTERVAL);
    }

    async FaceDetector(video, canvas) {
      var self = this;
      var image =  self.state.imageEl;

      if (!video || !this.isFaceDetectionModelLoaded() || self.descriptors.length === 0) {
          return setTimeout(() => this.FaceDetector(video, canvas), FACE_DETECTION_CONFIG.RECOGNITION.RETRY_DELAY);
      }

      var options = new self.faceapi.TinyFaceDetectorOptions();
      var maxDescriptorDistance = FACE_DETECTION_CONFIG.RECOGNITION.MAX_DESCRIPTOR_DISTANCE;

      var displaySize = { 
        width : self.state.videoElwidth,
        height : self.state.videoElheight,
      };

      try {
        self.faceapi.matchDimensions(canvas, displaySize);
        self.state.intervalID = setInterval(async () => {          
            canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
            const detections = await self.faceapi.detectSingleFace(video, options)
                .withFaceLandmarks()
                .withFaceDescriptor();
            if (detections) {
                const resizedDetections = faceapi.resizeResults(detections, displaySize);
                faceapi.draw.drawDetections(canvas, resizedDetections);
                faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

                var faceMatcher = new faceapi.FaceMatcher(self.descriptors, maxDescriptorDistance);
                const result = faceMatcher.findBestMatch(resizedDetections.descriptor);
                if (result && result._label != 'unknown' && result._distance < FACE_DETECTION_CONFIG.RECOGNITION.MAX_MATCH_DISTANCE) {
                    self.state.match_count.push(result._label);

                    var employee = result._label.split(',');
                    self.state.match_employee_id = employee[0];
                    var label = employee[1];

                    if (label) {
                        const box = resizedDetections.detection.box;
                        const drawBox = new faceapi.draw.DrawBox(box, { label: label.toString() });
                        drawBox.draw(canvas);
                    }

                    if (self.state.match_employee_id && self.state.match_count.length > FACE_DETECTION_CONFIG.RECOGNITION.MIN_MATCH_COUNT && !self.state.attendanceUpdated) {
                        self.state.attendanceUpdated = true; 
                        clearInterval(self.state.intervalID);
                        let { box } = resizedDetections.detection;
                        const padding = FACE_DETECTION_CONFIG.IMAGE_CAPTURE.FACE_PADDING;
                        let region = new faceapi.Rect(box.x-padding, box.y-padding, box.width+(padding*2), box.height+(padding*2));
                        let faces = await faceapi.extractFaces(video, [region]);

                        if (faces.length > 0) {
                            let faceCanvas = faces[0];
                            let faceBase64 = faceCanvas.toDataURL("image/jpeg");
                            faceBase64 = faceBase64.replace(/^data:image\/(png|jpg|jpeg);base64,/, "");
                            self.updateAttendance(self.state.match_employee_id, faceBase64);
                        }
                    }
                }
            }
        }, FACE_DETECTION_CONFIG.RECOGNITION.DETECTION_INTERVAL);
      } 
      catch (e) { console.error(e); }
    }

    onClose() {
      var self = this;
      if (window.stream) {
        window.stream.getTracks().forEach(track => track.stop());
      }
      if (self.state.intervalID) clearInterval(self.state.intervalID);
      self.props.close && self.props.close();
    }

    async updateAttendance(employee_id, image){
        if (!employee_id || !image) return;
        this.props.updateRecognitionAttendance({ employee_id, image });
        if (window.stream) {
            window.stream.getTracks().forEach(track => track.stop());
        }
        this.props.close();
    }

    isFaceDetectionModelLoaded() {
      return !!this.faceapi.nets.tinyFaceDetector.params;
    }
}

AttendanceRecognitionDialog.components = { Dialog };
AttendanceRecognitionDialog.template = "attendance_face_recognition.AttendanceRecognitionDialog";
AttendanceRecognitionDialog.defaultProps = {};
AttendanceRecognitionDialog.props = {
  faceapi: false,
  labeledFaceDescriptors : [],
  close: Function,
};
