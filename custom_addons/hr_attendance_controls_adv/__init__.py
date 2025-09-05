
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from . import controllers
from . import models

def uninstall_hook(env):
    env.cr.execute("UPDATE ir_act_window "
        "SET view_mode=replace(view_mode, ',geofence_view', '')"
        "WHERE view_mode LIKE '%,geofence_view%';")
    env.cr.execute("UPDATE ir_act_window "
        "SET view_mode=replace(view_mode, 'geofence_view,', '')"
        "WHERE view_mode LIKE '%geofence_view,%';")
    env.cr.execute("DELETE FROM ir_act_window "
        "WHERE view_mode = 'geofence_view';")

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie =version_info.get('server_serie')
    if server_serie!='18.0':
        raise UserError('Module support Odoo series 18.0 found {}.'.format(server_serie))
    return True