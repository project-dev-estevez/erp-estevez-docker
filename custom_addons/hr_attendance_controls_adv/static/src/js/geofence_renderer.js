/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, onMounted, useRef, useEffect, useState} from "@odoo/owl";

export class GeofenceRenderer extends Component {
    setup() {
        this.mapContainerRef = useRef("mapContainer");
        this.state = useState({
            olmap: null,
            drawingPath : 'overlay_paths',
        });
        useEffect(
            () => {
                this.state.olmap = new ol.Map({
                    layers: [
                        new ol.layer.Tile({
                            source: new ol.source.OSM(),
                        })],
                    view: new ol.View({
                        center: ol.proj.fromLonLat([0, 0]),
                        zoom: 0,
                    }),
                });
                this.state.olmap.setTarget(this.mapContainerRef.el);
                this.state.olmap.updateSize();
            },
            () => []
        );
        useEffect(() => {
            this.updateMap();
        });
        onMounted(async () => {
            this.onMounted();
        });
    }
    updateMap(){
        if (this.state.olmap){
            this.addLayerVector();
        }
    }
    onMounted() {
        if(this.state.olmap){
            this.state.olmap.updateSize();
        }
    }

    addLayerVector(){
        var self = this;
        if (self.state.olmap){
            
            var layersToRemove = [];
            self.state.olmap.getLayers().forEach(layer => {
                if (layer.get('name') != undefined && layer.get('name') === 'vectorSource') {
                    layersToRemove.push(layer);
                }
            });

            var len = layersToRemove.length;
            for(var i = 0; i < len; i++) {
                self.state.olmap.removeLayer(layersToRemove[i]);
            }

            self.props.model.data.records.forEach((record)=>{
                var value = record[self.state.drawingPath];
                if (Object.keys(value).length > 0) {  
                    var value = JSON.parse(value);
                    var vectorSource = new ol.layer.Vector({
                        source:new ol.source.Vector({
                            features:(new ol.format.GeoJSON()).readFeatures(value)
                        }),
                        style: new ol.style.Style({
                            fill: new ol.style.Fill({
                                color: 'rgb(255 235 59 / 62%)',
                            }),
                            stroke: new ol.style.Stroke({
                                color: '#ffc107',
                                width: 2,
                            }),
                            image: new ol.style.Circle({
                                radius: 7,
                                fill: new ol.style.Fill({
                                    color: '#ffc107',
                                }),
                            }),
                        }),
                    });
                    vectorSource.set('name', 'vectorSource');
                    self.state.olmap.addLayer(vectorSource);
                };
            });
            self.state.olmap.updateSize();
        }
    }
}

GeofenceRenderer.template = "hr_attendance_controls_adv.ViewRenderer";
GeofenceRenderer.props = {
    model: { type: Object },
};