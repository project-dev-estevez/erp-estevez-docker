/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { onMounted, useState, useRef, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AttendanceRecognitionDialog extends Component {
  setup() {
    this.title = _t("Face Recognition");

    this.videoRef = useRef("video");
    this.imageRef = useRef("image");
    this.canvasRef = useRef("canvas");
    this.selectRef = useRef("select");

    this.notificationService = useService('notification');

    this.state = useState({
      videoElwidth: 0,
      videoElheight: 0,
      intervalID: false,
      match_employee_id: false,
      match_count: [],
      attendanceUpdated: false,
      blinkCount: 0,
      eyeClosed: false,
      blinkTimeout: null,
      blinkWarning: false,
      eyeClosedFrames: 0,  // Contador de frames con ojos cerrados
      eyeOpenFrames: 0,    // Contador de frames con ojos abiertos
      waitingForOpenEyes: false,  // Flag para esperar que los ojos estén bien abiertos
      earHistory: [],      // Historial de EAR para calcular baseline dinámico
    })

    this.faceapi = this.props.faceapi;
    this.descriptors = this.props.labeledFaceDescriptors;

    onMounted(async () => {
      await this.loadWebcam();
    });
  }
  loadWebcam() {
    var self = this;
    if (navigator.mediaDevices) {
      var videoElement = this.videoRef.el;
      var imageElement = this.imageRef.el;
      var videoSelect = this.selectRef.el;
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
          video: { deviceId: videoSource ? { exact: videoSource } : undefined }
        };
        navigator.mediaDevices.getUserMedia(constraints).then(gotStream).then(gotDevices).catch(handleError);
      }

      function gotStream(stream) {
        window.stream = stream; // make stream available to console
        videoElement.srcObject = stream;
        // Refresh button list in case labels have become available
        videoElement.onloadedmetadata = function (e) {
          videoElement.play().then(function () {
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
    else {
      this.notificationService.add(
        _t("https Failed: Warning! WEBCAM MAY ONLY WORKS WITH HTTPS CONNECTIONS. So your Odoo instance must be configured in https mode."),
        { type: "danger" });
    }
  }
  onLoadStream() {
    var self = this;
    if (self.state.intervalID) {
      clearInterval(self.state.intervalID);
    }
    var video = self.state.videoEl;
    var canvas = self.canvasRef.el;
    self.FaceDetector(video, canvas);
  }
  async FaceDetector(video, canvas) {
    var self = this;
    var image = self.state.imageEl;

    if (video && video.paused || video && video.ended || !this.isFaceDetectionModelLoaded() || self.descriptors.length === 0) {
      return setTimeout(() => this.FaceDetector())
    }

    var options = this.getFaceDetectorOptions();
    var useTinyModel = true;
    var maxDescriptorDistance = 0.45;

    var displaySize = {
      width: self.state.videoElwidth,
      height: self.state.videoElheight,
    };

    try {
      self.faceapi.matchDimensions(canvas, displaySize);
      self.state.intervalID = setInterval(async () => {
        canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
        const detections = await self.faceapi.detectSingleFace(video, options)
          .withFaceLandmarks()
          .withFaceDescriptor();
        if (detections) {
          if (displaySize.width == 0 || displaySize.height == 0) {
            clearInterval(self.state.intervalID);
            return;
          }
          const resizedDetections = faceapi.resizeResults(detections, displaySize);
          faceapi.draw.drawDetections(canvas, resizedDetections);
          faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

          // 👁️ detección de parpadeo mejorada con anti-falsas detecciones
          if (resizedDetections.landmarks) {
            const leftEye = resizedDetections.landmarks.getLeftEye();
            const rightEye = resizedDetections.landmarks.getRightEye();
            if (Array.isArray(leftEye) && leftEye.length === 6 && Array.isArray(rightEye) && rightEye.length === 6) {
              const leftEAR = self.eyeAspectRatio(leftEye);
              const rightEAR = self.eyeAspectRatio(rightEye);
              const avgEAR = (leftEAR + rightEAR) / 2.0;
              
              // 🎯 CONFIGURACIÓN SIMPLIFICADA Y MÁS SENSIBLE
              const EYE_DIFFERENCE_MAX = 0.10;        // Más permisivo con diferencia entre ojos
              const MIN_CONSECUTIVE_CLOSED = 1;       // Reducido a 1 (parpadeos muy rápidos)
              const MIN_CONSECUTIVE_OPEN = 2;         // Reducido a 2 (parpadeos muy rápidos)
              
              // Verificar que ambos ojos parpadeen de forma similar (no es movimiento de cabeza)
              const eyeDifference = Math.abs(leftEAR - rightEAR);
              
              // 📊 Mantener historial de EAR para calcular baseline dinámico
              if (!self.state.earHistory) {
                self.state.earHistory = [];
              }
              
              self.state.earHistory.push(avgEAR);
              if (self.state.earHistory.length > 30) {
                self.state.earHistory.shift(); // Mantener últimos 30 valores
              }
              
              // Calcular baseline dinámico (promedio de los valores MÁS ALTOS = ojos bien abiertos)
              const earBaseline = self.state.earHistory.length > 10 
                ? self.state.earHistory.slice().sort((a, b) => b - a).slice(0, 10).reduce((a, b) => a + b) / 10
                : 0.28; // Valor por defecto
              
              // 🎯 Threshold dinámico: 98% del baseline (ajustado basado en tus logs reales)
              // Según tus logs: Baseline = 0.276, cuando parpadeas = 0.269
              // 0.269 / 0.276 = 97.4%, entonces usamos 98% para detectar
              // 0.276 * 0.98 = 0.270 (detectará cuando bajes a 0.269 o menos)
              const dynamicThreshold = earBaseline * 0.98;
              
              // Log SIEMPRE para que puedas ver los valores
              console.log(`[BLINK] EAR: ${avgEAR.toFixed(3)} | Baseline: ${earBaseline.toFixed(3)} | Threshold: ${dynamicThreshold.toFixed(3)} | LeftEAR: ${leftEAR.toFixed(3)} | RightEAR: ${rightEAR.toFixed(3)} | Diff: ${eyeDifference.toFixed(3)} | Closed: ${self.state.eyeClosedFrames} | Open: ${self.state.eyeOpenFrames} | Count: ${self.state.blinkCount}/3`);
              
              // 🎯 DETECCIÓN SIMPLIFICADA
              const isEyesClosed = avgEAR < dynamicThreshold && eyeDifference < EYE_DIFFERENCE_MAX;
              const isEyesOpen = avgEAR >= dynamicThreshold;
              
              if (isEyesClosed) {
                // Ojos están cerrados
                self.state.eyeClosedFrames++;
                self.state.eyeOpenFrames = 0;
                
                if (self.state.eyeClosedFrames >= MIN_CONSECUTIVE_CLOSED && !self.state.eyeClosed) {
                  self.state.eyeClosed = true;
                  console.log(`[BLINK] 👁️ ❌ Ojos CERRADOS detectados (EAR: ${avgEAR.toFixed(3)} < ${dynamicThreshold.toFixed(3)})`);
                }
              } else if (isEyesOpen) {
                // Ojos están abiertos
                self.state.eyeOpenFrames++;
                
                // Si estaba cerrado y ahora abrió durante varios frames, cuenta como parpadeo
                if (self.state.eyeClosed && self.state.eyeOpenFrames >= MIN_CONSECUTIVE_OPEN) {
                  self.state.eyeClosed = false;
                  self.state.eyeClosedFrames = 0;
                  self.state.blinkCount = (self.state.blinkCount || 0) + 1;
                  self.state.blinkWarning = false;
                  
                  console.log(`[BLINK] 👁️ ✅ Ojos ABIERTOS - PARPADEO #${self.state.blinkCount} REGISTRADO!`);
                  
                  // 🎯 Si es el tercer parpadeo, activa el flag de espera
                  if (self.state.blinkCount === 3) {
                    console.log(`[BLINK] 🎉 ¡Tercer parpadeo detectado! Esperando 500ms para que abras bien los ojos...`);
                    self.state.waitingForOpenEyes = true;
                    
                    // Espera 500ms para que los ojos estén bien abiertos antes de tomar la foto
                    setTimeout(() => {
                      self.state.waitingForOpenEyes = false;
                      console.log(`[BLINK] ✅ ¡Listo! Ahora puedes tomar la foto con los ojos abiertos`);
                    }, 1500);
                  } else {
                    console.log(`[BLINK] 🎉 Parpadeo válido detectado. Total: ${self.state.blinkCount}/3`);
                  }
                  
                  // Reinicia el timeout cada vez que parpadea
                  if (self.state.blinkTimeout) {
                    clearTimeout(self.state.blinkTimeout);
                  }
                  self.state.blinkTimeout = setTimeout(() => {
                    if (self.state.blinkCount < 3) {
                      self.state.blinkWarning = true;
                      self.state.blinkCount = 0; // Reinicia el contador
                    }
                  }, 15000); // 15 segundos para completar los 3 parpadeos
                } else if (!self.state.eyeClosed) {
                  // Resetea contador de frames cerrados si nunca llegó al mínimo
                  self.state.eyeClosedFrames = 0;
                }
              }
            } else {
              // Log: landmarks no válidos
              console.log('[BLINK] ⚠️ Landmarks de ojos no válidos');
              self.state.eyeClosedFrames = 0;
              self.state.eyeOpenFrames = 0;
            }
          }

          if (resizedDetections && Object.keys(resizedDetections).length > 0) {
            var faceMatcher = new faceapi.FaceMatcher(self.descriptors, maxDescriptorDistance);
            if (!faceMatcher || typeof faceMatcher === 'undefined' || faceMatcher === null) {
              return;
            }
            const result = faceMatcher.findBestMatch(resizedDetections.descriptor);
            if (result && result._label != 'unknown' && result._distance < 0.5) {
              if (self.state.match_count.length !== 'undefined') {
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

              // ✅ ahora exige 3 parpadeos además de reconocimiento facial
              // 🎯 Espera a que los ojos estén bien abiertos después del tercer parpadeo
              if (self.state.match_employee_id
                && self.state.match_count.length > 2
                && (self.state.blinkCount || 0) >= 3
                && !self.state.waitingForOpenEyes  // ← NUEVO: Espera que termine el delay
                && !self.state.attendanceUpdated) {
                self.state.attendanceUpdated = true;
                clearInterval(self.state.intervalID);
                if (self.state.blinkTimeout) {
                  clearTimeout(self.state.blinkTimeout);
                }
                console.log('[BLINK] 📸 Tomando foto con los ojos abiertos...');
                if (!self.state.intervalId) {
                  let { box } = resizedDetections.detection;
                  let region = new faceapi.Rect(box.x - 100, box.y - 100, box.width + 200, box.height + 200);
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
    catch (e) { }
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
  async updateAttendance(employee_id, image) {
    if (!employee_id || !image) {
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

  // Calcula el Eye Aspect Ratio (EAR) para detección de parpadeo
  eyeAspectRatio(eye) {
    // eye es un array de puntos [{x, y}, ...]
    const distV1 = Math.hypot(eye[1].x - eye[5].x, eye[1].y - eye[5].y);
    const distV2 = Math.hypot(eye[2].x - eye[4].x, eye[2].y - eye[4].y);
    const distH = Math.hypot(eye[0].x - eye[3].x, eye[0].y - eye[3].y);
    return (distV1 + distV2) / (2.0 * distH);
  }
}
AttendanceRecognitionDialog.components = { Dialog };
AttendanceRecognitionDialog.template = "attendance_face_recognition.AttendanceRecognitionDialog";
AttendanceRecognitionDialog.defaultProps = {};
AttendanceRecognitionDialog.props = {
  faceapi: false,
  labeledFaceDescriptors: [],
  close: Function,
}