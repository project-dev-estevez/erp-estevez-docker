/** @odoo-module */

import { registry } from "@web/core/registry"
import { loadJS } from "@web/core/assets"
const { Component, onWillStart, useRef, onMounted } = owl

export class ChartRenderer extends Component {
    setup(){
        this.chartRef = useRef("chart")
        onWillStart(async ()=>{
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
        })

        onMounted(()=>this.renderChart())
    }

    renderChart(){
      // Opciones por defecto
      const defaultOptions = {
          indexAxis: 'y',
          responsive: true,
          plugins: {
              legend: {
                  position: 'bottom',
              },
              title: {
                  display: true,
                  text: this.props.title,
                  position: 'bottom',
              }
          }
      };
      // Mezcla las opciones por defecto con las que recibes por props (si existen)
      const options = {
          ...defaultOptions,
          ...(this.props.config.options || {}),
          plugins: {
              ...defaultOptions.plugins,
              ...(this.props.config.options?.plugins || {}),
              legend: {
                  ...defaultOptions.plugins.legend,
                  ...(this.props.config.options?.plugins?.legend || {}),
              },
              title: {
                  ...defaultOptions.plugins.title,
                  ...(this.props.config.options?.plugins?.title || {}),
              }
          }
      };

      new Chart(this.chartRef.el, {
        type: this.props.type,
        data: this.props.config.data,
        options: options,
      }
    );
  }
}

ChartRenderer.template = "owl.ChartRenderer"