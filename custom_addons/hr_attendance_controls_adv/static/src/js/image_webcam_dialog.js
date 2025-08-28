/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useState, useRef, Component } from "@odoo/owl";

export class ImageWebcamDialog extends Component {
    setup() {
        this.title = _t("Capture Snapshot");

        this.videoRef = useRef("video");
        this.imageRef = useRef("image");
        this.selectRef = useRef("select");

        this.notificationService = useService('notification');
        
        onMounted(async () => {
            await this.loadWebcam();
        });        
    }
    loadWebcam(){
        if (navigator.mediaDevices) {
            
            var videoElement = this.videoRef.el;
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
            return self.notificationService.add(
              _t("https Failed: Warning! WEBCAM MAY ONLY WORKS WITH HTTPS CONNECTIONS. So your Odoo instance must be configured in https mode."), 
              { type: "danger" }
            );
        }
    }
    close() {
        this.props.close && this.props.close();
    }
    onClose() {
      var self = this;
      if (window.stream) {
        window.stream.getTracks().forEach(track => {
          track.stop();
        });
      }
      self.props.close && self.props.close();
    }
    onClickConfirm(){
      const video = this.videoRef.el;
      const image = this.imageRef.el;
      image.width = video.videoWidth;
      image.height = video.videoHeight;
      const context = image.getContext('2d');
      context.drawImage(video, 0, 0, image.width, image.height);
      const data = image.toDataURL("image/jpeg");
      this.props.uploadWebcamImage({
          data: data,
      });
      this.props.close();
  }
}
ImageWebcamDialog.components = { Dialog };
ImageWebcamDialog.template = "hr_attendance_controls_adv.ImageWebcamDialog";
ImageWebcamDialog.defaultProps = {};