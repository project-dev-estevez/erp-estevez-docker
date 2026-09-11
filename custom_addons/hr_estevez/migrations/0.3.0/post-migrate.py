# -*- coding: utf-8 -*-
"""Normaliza de forma retroactiva los teléfonos ya existentes en hr_employee.

Aplica la misma lógica que ``normalize_mx_phone`` (formato internacional con
espacios, +52 para números MX de 10 dígitos) sobre los registros que ya estaban
en la base antes de esta versión. Trabaja a nivel SQL para no disparar la
sincronización con System ni el tracking del chatter.
"""
import logging

from odoo.addons.hr_estevez.models.hr_employee import (
    EMPLOYEE_PHONE_FIELDS,
    normalize_mx_phone,
)

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cols = list(EMPLOYEE_PHONE_FIELDS)
    where = " OR ".join("(%s IS NOT NULL AND %s <> '')" % (c, c) for c in cols)
    cr.execute("SELECT id, %s FROM hr_employee WHERE %s" % (", ".join(cols), where))
    rows = cr.fetchall()
    _logger.info("hr_estevez 0.3.0: revisando teléfonos de %s empleados", len(rows))

    updated = 0
    for row in rows:
        emp_id, values = row[0], row[1:]
        changes = {}
        for col, value in zip(cols, values):
            new_value = normalize_mx_phone(value)
            if new_value != value:
                changes[col] = new_value
        if not changes:
            continue
        set_clause = ", ".join("%s = %%(%s)s" % (c, c) for c in changes)
        cr.execute(
            "UPDATE hr_employee SET %s WHERE id = %%(_id)s" % set_clause,
            dict(changes, _id=emp_id),
        )
        updated += 1

    _logger.info("hr_estevez 0.3.0: teléfonos normalizados en %s empleados", updated)
