/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { onMounted, useState, useRef, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AttendanceRecognitionDialog extends Component {
    setup() {

        this.videoRef = useRef("video");
        this.imageRef = useRef("image");
        this.canvasRef = useRef("canvas");
        this.selectRef = useRef("select");

        this.notificationService = useService('notification');

        this.state = useState({
          videoElwidth: 0,
          videoElheight: 0,
          intervalID: false,
          match_employee_id : false,
          match_count : [],
          attendanceUpdated: false,
        })

        this.faceapi = this.props.faceapi;
        this.descriptors = this.props.labeledFaceDescriptors;

        onMounted(async () => {
            await this.loadWebcam();            
        });  
    }
    loadWebcam(){
        var self = this;
        if (navigator.mediaDevices) {            
            var videoElement = this.videoRef.el;
            var imageElement = this.imageRef.el;
            var videoSelect =this.selectRef.el;
            const selectors = [videoSelect]

            startStream();

            videoSelect.onchange = startStream;
            navigator.mediaDevices.enumerateDevices().then(gotDevices).catch(handleError);

            function startStream() {
                if (window.stream) {
                  window.stream.getTracks().forEach(track => {
                    track.stop();
                  });
                }
                const videoSource = videoSelect.value;
                const constraints = {
                  video: {deviceId: videoSource ? {exact: videoSource} : undefined}
                };
                navigator.mediaDevices.getUserMedia(constraints).then(gotStream).then(gotDevices).catch(handleError);
            }

            function gotStream(stream) {
                window.stream = stream; // make stream available to console
                videoElement.srcObject = stream;
                // Refresh button list in case labels have become available
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
                // Handles being called several times to update labels. Preserve values.
                const values = selectors.map(select => select.value);
                selectors.forEach(select => {
                  while (select.firstChild) {
                    select.removeChild(select.firstChild);
                  }
                });
                for (let i = 0; i !== deviceInfos.length; ++i) {
                  const deviceInfo = deviceInfos[i];
                  const option = document.createElement('option');
                  option.value = deviceInfo.deviceId;
                  if (deviceInfo.kind === 'videoinput') {
                    option.text = deviceInfo.label || `camera ${videoSelect.length + 1}`;
                    videoSelect.appendChild(option);
                  } 
                  else {
                    // console.log('Some other kind of source/device: ', deviceInfo);
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
        else{
            this.notificationService.add(
              _t("https Failed: Warning! WEBCAM MAY ONLY WORKS WITH HTTPS CONNECTIONS. So your Odoo instance must be configured in https mode."), 
              { type: "danger" });
        }
    }
    onLoadStream(){
      var self = this;
      if (self.state.intervalID) {
          clearInterval(self.state.intervalID);
      }
      var video = self.state.videoEl;
      var canvas =self.canvasRef.el;
      self.FaceDetector(video, canvas);        
    }
    async FaceDetector(video, canvas) {
      var self = this;
      var image =  self.state.imageEl;

      if (video && video.paused || video && video.ended || !this.isFaceDetectionModelLoaded() || self.descriptors.length === 0) {
          return setTimeout(() => this.FaceDetector())
      }

      var options = this.getFaceDetectorOptions();
      var useTinyModel = true;
      var maxDescriptorDistance = 0.45;

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
                if(displaySize.width == 0 || displaySize.height == 0){
                    clearInterval(self.state.intervalID);
                    return
                }                
                const resizedDetections = faceapi.resizeResults(detections, displaySize);
                faceapi.draw.drawDetections(canvas, resizedDetections)
                faceapi.draw.drawFaceLandmarks(canvas, resizedDetections)

                if (resizedDetections && Object.keys(resizedDetections).length > 0) {
                    var faceMatcher = new faceapi.FaceMatcher(self.descriptors, maxDescriptorDistance);
                    if (!faceMatcher || typeof faceMatcher === 'undefined' || faceMatcher === null){
                      return;
                    }
                    const result = faceMatcher.findBestMatch(resizedDetections.descriptor);
                    if (result && result._label != 'unknown' && result._distance < 0.5) {
                        if (self.state.match_count.lenght != 'undefined') {
                            self.state.match_count.push(result._label);
                        } else if (self.match_count.includes(result._label)) {
                            self.state.match_count.push(result._label);
                        } else {
                            self.state.match_count = [];
                        }

                        var employee = result._label.split(',');
                        self.state.match_employee_id = employee[0];
                        var label = employee[1];

                        if (label) {
                            const box = resizedDetections.detection.box;
                            const drawBox = new faceapi.draw.DrawBox(box, { label: label.toString() });
                            drawBox.draw(canvas);
                        }

                        if (self.state.match_employee_id && self.state.match_count.length > 2 && !self.state.attendanceUpdated) {
                            self.state.attendanceUpdated = true; 
                            clearInterval(self.state.intervalID);
                            if (!self.state.intervalId) {
                                let { box } = resizedDetections.detection;
                                let region = new faceapi.Rect(box.x-100, box.y-100, box.width+200, box.height+200);
                                let faces = await faceapi.extractFaces(video, [region]);

                                if (faces.length > 0) {
                                    let faceCanvas = faces && faces[0];
                                    let faceBase64 = faceCanvas.toDataURL("image/jpeg");
                                    faceBase64 = faceBase64.replace(/^data:image\/(png|jpg|jpeg);base64,/, "");
                                    self.updateAttendance(self.state.match_employee_id, faceBase64);
                                }
                            }
                        }
                    }
                }
            }
        }, 200);
      } 
      catch (e) {}
    }
    onClose() {
      var self = this;
      if (window.stream) {
        window.stream.getTracks().forEach(track => {
          track.stop();
        });
      }
      if (self.state.intervalID) {
        clearInterval(self.state.intervalID);
      }
      self.props.close && self.props.close();
    }
    async updateAttendance(employee_id, image){
        if (!employee_id || !image){
          return;
        }
        
        this.props.updateRecognitionAttendance({
          'employee_id': employee_id,
          'image': image,
        });
        if (window.stream) {
            window.stream.getTracks().forEach(track => {
                track.stop();
            });
        }
        this.props.close();
    }
    getFaceDetectorOptions() {
      let inputSize = 384; // by 32, common sizes are 128, 160, 224, 320, 416, 512, 608,
      let scoreThreshold = 0.5;
      return new self.faceapi.TinyFaceDetectorOptions(); // {inputSize, scoreThreshold }
    }

    getCurrentFaceDetectionNet() {
      return self.faceapi.nets.tinyFaceDetector;
    }

    isFaceDetectionModelLoaded() {
      return !!this.getCurrentFaceDetectionNet().params
    }
}
AttendanceRecognitionDialog.components = { Dialog };
AttendanceRecognitionDialog.template = "attendance_face_recognition.AttendanceRecognitionDialog";
AttendanceRecognitionDialog.defaultProps = {};
AttendanceRecognitionDialog.props = {
  faceapi: false,
  labeledFaceDescriptors : [],
  close: Function,
}