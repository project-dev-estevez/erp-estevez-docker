odoo.define('custom_user_menu.hide_documentation', [], function(require) {
    'use strict';
    
    const { registry } = require('@web/core/registry');
    
    // Eliminar el ítem "Documentation" del registro de menú de usuario
    const userMenuRegistry = registry.category('user_menuitems');
    console.log(userMenuRegistry);
    userMenuRegistry.remove('documentation');
    userMenuRegistry.remove('support');
    userMenuRegistry.remove('odoo_account');
});