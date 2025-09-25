/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.state.currentMoment = this.state.currentMoment || 'unknown';
        console.log("[Estevez] setup ejecutado → currentMoment inicial:", this.state.currentMoment);
    },

    async searchReadEmployee() {
        // Llamar siempre al original
        if (typeof super.searchReadEmployee === "function") {
            await super.searchReadEmployee();
        }
        // Actualizar momento
        this._updateMoment();
        console.log("[Estevez] searchReadEmployee completado →", this.state.currentMoment);
    },

    _updateMoment() {
        if (this.state.checkedIn) {
            this.state.currentMoment = 'in_journey';
        } else if (!this.state.checkedIn && this.isFirstAttendance) {
            this.state.currentMoment = 'before_first_checkin';
        } else if (!this.state.checkedIn && !this.isFirstAttendance) {
            this.state.currentMoment = 'after_check_out';
        } else {
            this.state.currentMoment = 'unknown';
        }
        console.log("[Estevez] _updateMoment →", {
            checkedIn: this.state.checkedIn,
            isFirstAttendance: this.isFirstAttendance,
            currentMoment: this.state.currentMoment,
        });
    },
});

export default ActivityMenu;
