/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { onMounted, useState, useRef, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AttendanceWebcamDialog extends Component {
    setup() {
        this.title = _t("Capture Snapshot");

        this.videoRef = useRef("video");
        this.imageRef = useRef("image");
        this.selectRef = useRef("select");

        this.notificationService = useService('notification');

        this.state = useState({
            videoEl: false,
            imageEl: false,
            videoElwidth: 0,
            videoElheight: 0,
        })

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
                    videoElement.play();
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
            this.notificationService.add(_t("https Failed: Warning! WEBCAM MAY ONLY WORKS WITH HTTPS CONNECTIONS. So your Odoo instance must be configured in https mode."), { type: "danger" });
        }
    }
    close() {
        this.props.close && this.props.close();
    }
    async onClickConfirm(){
        var video = this.state.videoEl;
        if (this.state.videoElwidth && this.state.videoElheight){
          var image = this.state.imageEl;
          image.width = this.state.videoElwidth;
          image.height = this.state.videoElheight;

          image.getContext('2d').drawImage(video, 0, 0, image.width, image.height);
          var img64 = image.toDataURL("image/jpeg");
          img64 = img64.replace(/^data:image\/(png|jpg|jpeg);base64,/, "");
          await this.props.uploadWebcamImage({
              image: img64,
          });
        }
        if (window.stream) {
            window.stream.getTracks().forEach(track => {
                track.stop();
            });
        }

        this.props.close();
    }
}
AttendanceWebcamDialog.components = { Dialog };
AttendanceWebcamDialog.template = "hr_attendance_controls_adv.AttendanceWebcamDialog";
AttendanceWebcamDialog.defaultProps = {};
AttendanceWebcamDialog.props = {};