# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

def migrate(cr, version):
    _logger.info(f'Starting migration from version {version}.')
    
    # Verificar el tipo de columna
    cr.execute("""
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'hr_employee' AND column_name = 'infonavit'
    """)
    column_type = cr.fetchone()[0]
    
    if column_type == 'character varying':
        cr.execute("""
            UPDATE hr_employee
            SET infonavit = CASE
                WHEN infonavit = 'SI' THEN TRUE
                WHEN infonavit = 'NO' THEN FALSE
                ELSE NULL
            END
        """)
        _logger.info('Migration completed.')
    else:
        _logger.info('No migration needed, infonavit is already a boolean.')