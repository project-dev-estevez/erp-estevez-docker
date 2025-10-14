/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { onMounted, useState, useRef, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { FACE_DETECTION_CONFIG, FACE_DETECTION_MESSAGES, DETECTION_PHASES } from "./attendance_recognition_config";

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
        currentPhase: DETECTION_PHASES.INITIAL_RECOGNITION,
        authorizedEmployeeId: null,
        authorizedEmployeeName: null,
        initialRecognitionCount: 0,
        initialRecognitionTimer: null,
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

    async initialRecognition() {
        console.log('🔍 Iniciando reconocimiento inicial del empleado...');
        
        const video = this.videoRef.el;
        if (!video) {
            console.error('❌ Video element no disponible');
            return;
        }

        const detection = await this.faceapi
            .detectSingleFace(video, new this.faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptor();

        if (!detection) {
            console.log('⚠️ No se detectó cara en reconocimiento inicial');
            return;
        }

        const bestMatch = this.descriptors.reduce((prev, curr) => {
            const distance = this.faceapi.euclideanDistance(detection.descriptor, curr.descriptors[0]);
            return distance < prev.distance ? { labeledDescriptor: curr, distance } : prev;
        }, { distance: Infinity });

        if (bestMatch.distance <= FACE_DETECTION_CONFIG.RECOGNITION.INITIAL_DISTANCE) {
            this.state.initialRecognitionCount++;
            console.log(`✅ Reconocimiento inicial ${this.state.initialRecognitionCount}/3: ${bestMatch.labeledDescriptor.label} (distancia: ${bestMatch.distance.toFixed(3)})`);
            
            if (this.state.initialRecognitionCount >= 3) {
                console.log('🎯 ¡Empleado autorizado! Pasando a fase de sonrisa...');
                
                // Limpiar timer de timeout ya que se identificó exitosamente
                if (this.state.initialRecognitionTimer) {
                    clearTimeout(this.state.initialRecognitionTimer);
                    this.state.initialRecognitionTimer = null;
                }
                
                // Extraer ID y nombre del empleado del label
                const employeeParts = bestMatch.labeledDescriptor.label.split(',');
                this.state.authorizedEmployeeId = employeeParts[0]; // Solo el ID: "3"
                this.state.authorizedEmployeeName = employeeParts[1] || bestMatch.labeledDescriptor.label; // El nombre o label completo
                this.state.currentPhase = DETECTION_PHASES.SMILE_VALIDATION;
                this.detectSmile();
                return;
            }
        } else {
            console.log(`❌ Reconocimiento fallido. Distancia: ${bestMatch.distance.toFixed(3)} > ${FACE_DETECTION_CONFIG.RECOGNITION.INITIAL_DISTANCE}`);
            this.state.initialRecognitionCount = 0;
        }

        // Continuar con el reconocimiento inicial
        setTimeout(() => this.initialRecognition(), 500);
    }

    _handleInitialRecognitionTimeout() {
        console.log('⏰ Timeout: No se pudo identificar empleado en 10 segundos');
        
        // Limpiar cualquier proceso activo
        if (this.state.intervalID) {
            clearInterval(this.state.intervalID);
            this.state.intervalID = false;
        }
        
        // Mostrar notificación de error
        this.notificationService.add(
            FACE_DETECTION_MESSAGES.INITIAL_RECOGNITION_TIMEOUT, 
            { type: "danger" }
        );
        
        // Cerrar el modal después de un breve delay
        setTimeout(() => {
            this.onClose();
        }, 2000); // 2 segundos para que el usuario lea la notificación
    }

    onLoadStream(){
      var self = this;
      if (self.state.intervalID) clearInterval(self.state.intervalID);
      
      console.log('🚀 Iniciando sistema de reconocimiento seguro...');
      console.log('📋 Fase actual:', self.state.currentPhase);
      
      // Comenzar con reconocimiento inicial del empleado
      if (self.state.currentPhase === DETECTION_PHASES.INITIAL_RECOGNITION) {
        console.log('🔐 Iniciando fase de reconocimiento inicial...');
        
        // Iniciar timer de timeout para reconocimiento inicial
        self.state.initialRecognitionTimer = setTimeout(() => {
          self._handleInitialRecognitionTimeout();
        }, FACE_DETECTION_CONFIG.RECOGNITION.INITIAL_TIMEOUT);
        
        self.initialRecognition();
      }
    }

    async detectSmile() {
      var self = this;
      const video = self.state.videoEl;
      const canvas = self.canvasRef.el;
      
      if (!video || !this.isFaceDetectionModelLoaded()) return;

      console.log('😊 Iniciando detección de sonrisa para empleado autorizado:', self.state.authorizedEmployeeName);

      var displaySize = { 
        width : self.state.videoElwidth,
        height : self.state.videoElheight,
      };
      self.faceapi.matchDimensions(canvas, displaySize);

      self.state.intervalID = setInterval(async () => {
          const detections = await self.faceapi
            .detectSingleFace(video, new self.faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceExpressions()
            .withFaceDescriptor();

          if (detections) {
              // Verificar que la persona sigue siendo la misma empleada autorizada
              const bestMatch = self.descriptors.reduce((prev, curr) => {
                  const distance = self.faceapi.euclideanDistance(detections.descriptor, curr.descriptors[0]);
                  return distance < prev.distance ? { labeledDescriptor: curr, distance } : prev;
              }, { distance: Infinity });

              // Si detectamos a una persona diferente, reiniciar el proceso
              const detectedEmployeeId = bestMatch.labeledDescriptor.label.split(',')[0];
              if (detectedEmployeeId !== self.state.authorizedEmployeeId || 
                  bestMatch.distance > FACE_DETECTION_CONFIG.RECOGNITION.SMILE_VALIDATION_DISTANCE) {
                  console.log(`⚠️ Persona diferente detectada durante la sonrisa. Autorizado: ${self.state.authorizedEmployeeId}, Detectado: ${detectedEmployeeId}. Reiniciando...`);
                  self._resetToInitialRecognition();
                  return;
              }

              // Procesar sonrisa solo del empleado autorizado
              const happyScore = detections.expressions.happy || 0;
              if (happyScore > FACE_DETECTION_CONFIG.SMILE.HAPPINESS_THRESHOLD) {
                  self.state.smiling = true;
                  self.state.smileTime += FACE_DETECTION_CONFIG.SMILE.TIME_INCREMENT;
                  console.log(`😊 Sonrisa detectada: ${happyScore.toFixed(3)} (${(self.state.smileTime/10).toFixed(1)}s/${FACE_DETECTION_CONFIG.SMILE.REQUIRED_DURATION/10}s)`);
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
                  console.log('✅ Fase de sonrisa completada. Pasando a reconocimiento final...');
                  self.state.currentPhase = DETECTION_PHASES.FINAL_RECOGNITION;
                  self.notificationService.add( FACE_DETECTION_MESSAGES.SMILE_SUCCESS, {type: "success"} );
                  setTimeout(() => self.FaceDetector(), FACE_DETECTION_CONFIG.UI.SMILE_COMPLETION_DELAY);
              }
          }
      }, FACE_DETECTION_CONFIG.SMILE.DETECTION_INTERVAL);
    }

    _resetToInitialRecognition() {
        console.log('🔄 Reiniciando a reconocimiento inicial por cambio de persona');
        
        // Limpiar intervalos activos
        if (this.state.intervalID) {
            clearInterval(this.state.intervalID);
            this.state.intervalID = false;
        }
        
        // Limpiar timer de timeout
        if (this.state.initialRecognitionTimer) {
            clearTimeout(this.state.initialRecognitionTimer);
            this.state.initialRecognitionTimer = null;
        }
        
        // Resetear estado de seguridad
        this.state.currentPhase = DETECTION_PHASES.INITIAL_RECOGNITION;
        this.state.authorizedEmployeeId = null;
        this.state.authorizedEmployeeName = null;
        this.state.initialRecognitionCount = 0;
        
        // Resetear estado de sonrisa
        this.state.smileTime = 0;
        this.state.smiling = false;
        this.state.progressPercent = 0;
        this.state.smilePhaseCompleted = false;
        
        // Resetear estado de reconocimiento
        this.state.match_employee_id = false;
        this.state.match_count = [];
        this.state.attendanceUpdated = false;
        
        // Limpiar barra de progreso
        if (this.progressRef.el) {
            this.progressRef.el.style.width = '0%';
        }
        
        // Reiniciar el proceso
        console.log('🚀 Reiniciando proceso de reconocimiento...');
        
        // Reiniciar timer de timeout
        this.state.initialRecognitionTimer = setTimeout(() => {
            this._handleInitialRecognitionTimeout();
        }, FACE_DETECTION_CONFIG.RECOGNITION.INITIAL_TIMEOUT);
        
        this.initialRecognition();
    }

    async FaceDetector() {
      var self = this;
      var video = self.state.videoEl;
      var canvas = self.canvasRef.el;
      var image =  self.state.imageEl;

      if (!video || !this.isFaceDetectionModelLoaded() || self.descriptors.length === 0) {
          return setTimeout(() => this.FaceDetector(), FACE_DETECTION_CONFIG.RECOGNITION.RETRY_DELAY);
      }

      console.log('🔍 Iniciando reconocimiento final para empleado autorizado:', self.state.authorizedEmployeeName);

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
                const resizedDetections = self.faceapi.resizeResults(detections, displaySize);
                self.faceapi.draw.drawDetections(canvas, resizedDetections);
                self.faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

                // Verificar que sigue siendo el mismo empleado autorizado
                const bestMatch = self.descriptors.reduce((prev, curr) => {
                    const distance = self.faceapi.euclideanDistance(detections.descriptor, curr.descriptors[0]);
                    return distance < prev.distance ? { labeledDescriptor: curr, distance } : prev;
                }, { distance: Infinity });

                // Si detectamos a una persona diferente, reiniciar
                const detectedEmployeeIdFinal = bestMatch.labeledDescriptor.label.split(',')[0];
                if (detectedEmployeeIdFinal !== self.state.authorizedEmployeeId || 
                    bestMatch.distance > FACE_DETECTION_CONFIG.RECOGNITION.FINAL_VALIDATION_DISTANCE) {
                    console.log(`⚠️ Persona diferente detectada en reconocimiento final. Autorizado: ${self.state.authorizedEmployeeId}, Detectado: ${detectedEmployeeIdFinal}. Reiniciando...`);
                    self._resetToInitialRecognition();
                    return;
                }

                var faceMatcher = new self.faceapi.FaceMatcher(self.descriptors, maxDescriptorDistance);
                const result = faceMatcher.findBestMatch(resizedDetections.descriptor);
                
                if (result && result._label != 'unknown' && result._distance < FACE_DETECTION_CONFIG.RECOGNITION.MAX_MATCH_DISTANCE) {
                    // Validar que el empleado reconocido es el autorizado
                    var employee = result._label.split(',');
                    var recognizedEmployeeId = employee[0];
                    
                    if (recognizedEmployeeId !== self.state.authorizedEmployeeId) {
                        console.log('⚠️ Empleado reconocido diferente al autorizado. Reiniciando...');
                        self._resetToInitialRecognition();
                        return;
                    }

                    self.state.match_count.push(result._label);
                    self.state.match_employee_id = employee[0];
                    var label = employee[1];

                    console.log(`✅ Reconocimiento final ${self.state.match_count.length}/3: ${label} (distancia: ${result._distance.toFixed(3)})`);

                    if (label) {
                        const box = resizedDetections.detection.box;
                        const drawBox = new self.faceapi.draw.DrawBox(box, { label: label.toString() });
                        drawBox.draw(canvas);
                    }

                    if (self.state.match_employee_id && self.state.match_count.length > FACE_DETECTION_CONFIG.RECOGNITION.MIN_MATCH_COUNT && !self.state.attendanceUpdated) {
                        self.state.attendanceUpdated = true; 
                        self.state.currentPhase = DETECTION_PHASES.COMPLETED;
                        clearInterval(self.state.intervalID);
                        
                        console.log('🎉 ¡Proceso de reconocimiento seguro completado exitosamente!');
                        
                        let { box } = resizedDetections.detection;
                        const padding = FACE_DETECTION_CONFIG.IMAGE_CAPTURE.FACE_PADDING;
                        let region = new self.faceapi.Rect(box.x-padding, box.y-padding, box.width+(padding*2), box.height+(padding*2));
                        let faces = await self.faceapi.extractFaces(video, [region]);

                        if (faces.length > 0) {
                            let faceCanvas = faces[0];
                            let faceBase64 = faceCanvas.toDataURL("image/jpeg");
                            faceBase64 = faceBase64.replace(/^data:image\/(png|jpg|jpeg);base64,/, "");
                            self.updateAttendance(self.state.match_employee_id, faceBase64);
                        }
                    }
                } else {
                    console.log('❌ Reconocimiento final fallido, continuando...');
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
      
      // Limpiar timer de timeout si existe
      if (self.state.initialRecognitionTimer) {
        clearTimeout(self.state.initialRecognitionTimer);
        self.state.initialRecognitionTimer = null;
      }
      
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
