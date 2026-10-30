# -*- coding: utf-8 -*-
"""Quita las MAYÚSCULAS de la información personal y de los catálogos geográficos.

1. Empleados: aplica ``normalize_capital_case`` a los campos de texto libre de
   ``EMPLOYEE_CAPITAL_CASE_FIELDS`` que estén TODO EN MAYÚSCULAS.
2. Catálogos ``hr.state`` / ``hr.municipality``: reemplaza los nombres por los de
   ``nombres_estados_municipios.csv`` (nombres oficiales del INEGI con acentos,
   precalculados). Los que no aparezcan en el archivo pasan a formato título.

Trabaja a nivel SQL para no disparar la sincronización con System. A System se
siguen enviando estado y municipio en mayúsculas sin acentos (``normalize_text``).
"""
import csv
import logging
import os
import unicodedata

from odoo.addons.hr_estevez.models.hr_employee import (
    EMPLOYEE_CAPITAL_CASE_FIELDS,
    normalize_capital_case,
)

_logger = logging.getLogger(__name__)


def _key(text):
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('utf-8')
    return ' '.join(text.upper().split())


def _migrate_employees(cr):
    cols = list(EMPLOYEE_CAPITAL_CASE_FIELDS)
    where = " OR ".join("(%s IS NOT NULL AND %s <> '')" % (c, c) for c in cols)
    cr.execute("SELECT id, %s FROM hr_employee WHERE %s" % (", ".join(cols), where))
    updated = 0
    for row in cr.fetchall():
        emp_id, values = row[0], row[1:]
        changes = {}
        for col, value in zip(cols, values):
            new_value = normalize_capital_case(value)
            if new_value != value:
                changes[col] = new_value
        if not changes:
            continue
        set_clause = ", ".join("%s = %%(%s)s" % (c, c) for c in changes)
        cr.execute("UPDATE hr_employee SET %s WHERE id = %%(id)s" % set_clause, dict(changes, id=emp_id))
        updated += 1
    _logger.info("hr_estevez 0.5.0: texto personal convertido en %s empleados", updated)


def _migrate_catalogs(cr):
    path = os.path.join(os.path.dirname(__file__), 'nombres_estados_municipios.csv')
    state_names, municipality_names = {}, {}
    with open(path, encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            if row['municipio']:
                municipality_names[(_key(row['estado']), _key(row['municipio']))] = row['nombre']
            else:
                state_names[_key(row['estado'])] = row['nombre']

    cr.execute("SELECT id, name FROM hr_state")
    states = cr.fetchall()
    state_key = {state_id: _key(name) for state_id, name in states}

    # Municipios primero: se buscan con el nombre del estado antes de cambiarlo
    cr.execute("SELECT id, name, state_id FROM hr_municipality")
    fallback = 0
    for mun_id, name, state_id in cr.fetchall():
        new_name = municipality_names.get((state_key.get(state_id), _key(name)))
        if not new_name:
            new_name = normalize_capital_case(name)
            fallback += new_name != name
        if new_name != name:
            cr.execute("UPDATE hr_municipality SET name = %s WHERE id = %s", (new_name, mun_id))

    for state_id, name in states:
        new_name = state_names.get(state_key[state_id]) or normalize_capital_case(name)
        if new_name != name:
            cr.execute("UPDATE hr_state SET name = %s WHERE id = %s", (new_name, state_id))

    _logger.info(
        "hr_estevez 0.5.0: catálogos actualizados (%s estados, %s municipios; %s sin nombre oficial)",
        len(states), len(municipality_names), fallback,
    )


def migrate(cr, version):
    if not version:
        return
    _migrate_employees(cr)
    _migrate_catalogs(cr)
