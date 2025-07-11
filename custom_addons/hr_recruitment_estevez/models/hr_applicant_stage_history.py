from odoo import models, fields, api

class HrApplicantStageHistory(models.Model):
    """
    Modelo para rastrear el historial completo de etapas de cada candidato.
    
    Permite calcular tiempos precisos por etapa y detectar cuellos de botella
    en el proceso de reclutamiento.
    """
    _name = 'hr.applicant.stage.history'
    _description = 'Historial de Etapas del Candidato'
    _order = 'applicant_id, enter_date desc'
    
    # === CAMPOS PRINCIPALES ===
    applicant_id = fields.Many2one(
        'hr.applicant', 
        string='Candidato',
        required=True, 
        ondelete='cascade',
        index=True,
        help='Candidato al que pertenece este registro de historial'
    )
    
    stage_id = fields.Many2one(
        'hr.recruitment.stage', 
        string='Etapa',
        required=True,
        index=True,
        help='Etapa del proceso de reclutamiento'
    )
    
    # === CAMPOS DE TIEMPO ===
    enter_date = fields.Datetime(
        string='Fecha de Entrada',
        required=True,
        default=fields.Datetime.now,
        help='Fecha y hora cuando el candidato entró a esta etapa'
    )
    
    leave_date = fields.Datetime(
        string='Fecha de Salida',
        help='Fecha y hora cuando el candidato salió de esta etapa. Vacío si sigue en la etapa.'
    )
    
    # === CAMPOS CALCULADOS ===
    duration_hours = fields.Float(
        string='Duración (Horas)',
        compute='_compute_duration',
        store=True,
        help='Tiempo en horas que el candidato estuvo en esta etapa'
    )
    
    duration_days = fields.Float(
        string='Duración (Días)',
        compute='_compute_duration',
        store=True,
        help='Tiempo en días que el candidato estuvo en esta etapa'
    )
    
    is_current_stage = fields.Boolean(
        string='Etapa Actual',
        compute='_compute_is_current_stage',
        store=True,
        help='True si esta es la etapa actual del candidato'
    )
    
    # === MÉTODOS COMPUTE ===
    @api.depends('enter_date', 'leave_date')
    def _compute_duration(self):
        """Calcula la duración en horas y días"""
        for record in self:
            if record.enter_date:
                end_time = record.leave_date or fields.Datetime.now()
                delta = end_time - record.enter_date
                
                # Convertir a horas y días
                total_seconds = delta.total_seconds()
                record.duration_hours = total_seconds / 3600
                record.duration_days = total_seconds / (24 * 3600)
            else:
                record.duration_hours = 0.0
                record.duration_days = 0.0
    
    @api.depends('applicant_id.stage_id', 'stage_id', 'leave_date')
    def _compute_is_current_stage(self):
        """Determina si esta es la etapa actual del candidato"""
        for record in self:
            record.is_current_stage = (
                record.stage_id == record.applicant_id.stage_id and 
                not record.leave_date
            )