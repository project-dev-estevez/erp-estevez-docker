# -*- coding: utf-8 -*-
"""Pasa ``hr_employee.registro_patronal`` (Selection) al catálogo ``hr.registro.patronal``.

Los registros iniciales ya fueron creados por ``data/hr_registro_patronal_data.xml``;
si algún empleado tiene un código que no está en el catálogo, se crea con el código
como descripción para no perder el dato. Corre antes de que Odoo elimine la
columna vieja al final de la actualización.
Trabaja a nivel SQL para no disparar la sincronización con System.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'hr_employee' AND column_name = 'registro_patronal'
    """)
    if not cr.fetchone():
        return

    cr.execute("""
        INSERT INTO hr_registro_patronal (code, name, active, create_uid, write_uid, create_date, write_date)
        SELECT DISTINCT e.registro_patronal, e.registro_patronal, true, 1, 1,
               now() at time zone 'UTC', now() at time zone 'UTC'
        FROM hr_employee e
        WHERE e.registro_patronal IS NOT NULL AND e.registro_patronal <> ''
          AND NOT EXISTS (SELECT 1 FROM hr_registro_patronal r WHERE r.code = e.registro_patronal)
    """)
    if cr.rowcount:
        _logger.warning("hr_estevez 0.4.0: se crearon %s registros patronales fuera del catálogo inicial", cr.rowcount)

    cr.execute("""
        UPDATE hr_employee e
        SET registro_patronal_id = r.id
        FROM hr_registro_patronal r
        WHERE r.code = e.registro_patronal AND e.registro_patronal_id IS NULL
    """)
    _logger.info("hr_estevez 0.4.0: registro patronal asignado a %s empleados", cr.rowcount)
