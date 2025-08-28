/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadCSS, loadJS , AssetsLoadingError} from '@web/core/assets';
import { useModelWithSampleData } from "@web/model/model";
import { standardViewProps } from "@web/views/standard_view_props";
import { useSetupAction } from "@web/search/action_hook";
import { Layout } from "@web/search/layout";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";
import { Component, onWillStart} from "@odoo/owl";

const { DateTime } = luxon;

export class GeofenceController extends Component {
    setup() {
        const Model = this.props.Model;
        const model = useModelWithSampleData(Model, this.props.modelParams);
        this.model = model;

        useSetupAction({
            getLocalState: () => {
                return this.model.metaData;
            },
        });
        
        onWillStart(async () => {
            try {
                await loadCSS('/hr_attendance_controls_adv/static/src/lib/ol-6.12.0/ol.css');
                await loadCSS('/hr_attendance_controls_adv/static/src/lib/ol-ext/ol-ext.css');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-6.12.0/ol.js');
                await loadJS('/hr_attendance_controls_adv/static/src/lib/ol-ext/ol-ext.js');
            } catch (error) {
                if (!(error instanceof AssetsLoadingError)) {
                    throw error;
                }
            }
        });

        this.searchBarToggler = useSearchBarToggler();
    }

    get rendererProps() {
        return {
            model: this.model,
        };
    }
}

GeofenceController.template = "hr_attendance_controls_adv.Contoller";
GeofenceController.components = {
    Layout,
    SearchBar,
};

GeofenceController.props = {
    ...standardViewProps,
    Model: Function,
    modelParams: Object,
    Renderer: Function,
    buttonTemplate: String,
};
