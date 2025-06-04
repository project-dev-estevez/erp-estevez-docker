odoo.define('hr_recruitment_estevez.tabs_navigation', function(require) {
    "use strict";

    var FormController = require('web.FormController');

    FormController.include({
        /**
         * @override
         */
        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                // Añadir evento click a las pestañas
                self.$('.o_wizard_nav .nav-link').click(self._onTabClick.bind(self));
            });
        },

        _onTabClick: function(ev) {
            ev.preventDefault();
            var $tab = $(ev.currentTarget);
            var step = $tab.data('step');
            
            if (step) {
                this._rpc({
                    model: this.modelName,
                    method: 'set_wizard_step',
                    args: [this.handle, step],
                }).then(function() {
                    this.reload();
                }.bind(this));
            }
        }
    });
});