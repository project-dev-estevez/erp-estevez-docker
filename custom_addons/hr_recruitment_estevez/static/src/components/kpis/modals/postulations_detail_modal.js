/** @odoo-module **/

import { Component } from "@odoo/owl";

export class PostulationsDetailModal extends Component {
    static template = "hr_recruitment_estevez.PostulationsDetailModal";
    static props = {
        onClose: { type: Function }
    };

    onCloseModal() {
        console.log("🔴 Modal: Cerrando modal");
        this.props.onClose();
    }
}