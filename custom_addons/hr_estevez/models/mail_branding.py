# -*- coding: utf-8 -*-
"""Homologación de los correos que envía el sistema con la marca Estevez.Jor.

- Botones/enlaces: el morado de Odoo (#875A7B, #714B67) se cambia por el azul de
  Estevez.Jor (#239FD3, el azul del logo).
- Pie "Powered by Odoo" / "Con la tecnología de Odoo" -> "Con la tecnología de Estevez.Jor".
- Asunto del correo de restablecer contraseña: "Solicitud de restablecimiento de contraseña".

Los colores y el pie se aplican al cuerpo final de cada correo justo antes de enviarlo
(``mail.mail._prepare_outgoing_body``), así cubren todas las plantillas (QWeb y
``mail.template``), en cualquier idioma y aunque sean ``noupdate``. Además se configura
el color de botones de correo de la compañía para que las vistas previas en Odoo
también salgan en azul.
"""
import re

from odoo import api, models

ESTEVEZ_EMAIL_BLUE = '#239FD3'
ODOO_EMAIL_COLORS = ('#875A7B', '#714B67')
RESET_PASSWORD_SUBJECT = 'Solicitud de restablecimiento de contraseña'

_ODOO_COLOR_RE = re.compile(
    r'#(?:%s)\b' % '|'.join(color[1:] for color in ODOO_EMAIL_COLORS), re.IGNORECASE)

# "Powered by <a ...>Odoo</a>" y sus traducciones (es, es_419, es_MX...). El texto
# puede venir con la "í" literal o como entidad HTML según cómo se serializó.
_I = r'(?:í|i|&iacute;|&#237;|&#xed;)'
_POWERED_BY_RE = re.compile(
    r'(?:Powered\s+by|Con\s+la\s+tecnolog%(i)sa\s+de|Con\s+tecnolog%(i)sa\s+de|'
    r'Desarrollado\s+por|Impulsado\s+por|Creado\s+con)'
    r'\s*<a\b[^>]*>\s*Odoo\s*</a>' % {'i': _I},
    re.IGNORECASE,
)
_POWERED_BY_ESTEVEZ = (
    'Con la tecnología de <span style="color: %s; font-weight: bold;">Estevez.Jor</span>'
    % ESTEVEZ_EMAIL_BLUE
)


def apply_estevez_email_branding(body):
    """Devuelve ``body`` con el azul y el pie de Estevez.Jor."""
    if not body:
        return body
    body = _ODOO_COLOR_RE.sub(ESTEVEZ_EMAIL_BLUE, body)
    return _POWERED_BY_RE.sub(_POWERED_BY_ESTEVEZ, body)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        subject = self.env.context.get('estevez_reset_password_subject')
        if subject:
            for vals in vals_list:
                vals['subject'] = subject
        return super().create(vals_list)

    def _prepare_outgoing_body(self):
        return apply_estevez_email_branding(super()._prepare_outgoing_body())


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _action_reset_password(self, signup_type="reset"):
        # En modo creación de usuario Odoo usa la plantilla de invitación
        # (auth_signup.set_password_email) y su asunto no se toca. En otro caso el único
        # correo que se genera es el de restablecer contraseña.
        if self.env.context.get('create_user'):
            return super()._action_reset_password(signup_type=signup_type)
        return super(ResUsers, self.with_context(
            estevez_reset_password_subject=RESET_PASSWORD_SUBJECT,
        ))._action_reset_password(signup_type=signup_type)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _apply_estevez_email_colors(self):
        """Color de botones de correo de la compañía = azul Estevez.Jor, salvo que
        alguien ya haya elegido otro color distinto al morado de Odoo."""
        odoo_colors = {color.lower() for color in ODOO_EMAIL_COLORS}
        companies = self.sudo().with_context(active_test=False).search([])
        companies.filtered(
            lambda c: not c.email_secondary_color or c.email_secondary_color.lower() in odoo_colors
        ).write({'email_secondary_color': ESTEVEZ_EMAIL_BLUE})
