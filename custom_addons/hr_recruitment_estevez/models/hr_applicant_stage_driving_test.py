from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrApplicantStageDrivingTest(models.Model):
    
    _inherit = 'hr.applicant'

    # Prueba de manejo
    is_driving_test = fields.Boolean(
        compute='_compute_is_driving_test',
        store=False
    )

    is_driving_test_editable = fields.Boolean(
        string='Es Editable Prueba de Manejo',
        compute='_compute_is_driving_test_editable',
        store=False
    )

    evaluator_id = fields.Many2one(
        'res.users',
        string='Evaluador Asignado',
        default=lambda self: self.env.user,
    )

    evaluator_job_title = fields.Char(
        string='Puesto del Evaluador',
        compute='_compute_evaluator_job_title',
        store=True,
        readonly=True
    )

    license_type = fields.Selection([
        ('tipo_a', 'Tipo A'),
        ('tipo_b', 'Tipo B'),
        ('tipo_c', 'Tipo C'),
        ('tipo_d', 'Tipo D'),
        ('tipo_e', 'Tipo E'),
        ('tipo_e_federal', 'Tipo E (Federal)'),
        ('permiso_provisional', 'Permiso Provisional'),
    ], string='Tipo de Licencia')

    license_description = fields.Text(
        string='Descripción de la Licencia',
        compute='_compute_license_description',
        store=False,
        readonly=True
    )

    license_number = fields.Char(string='Número de Licencia')

    unit_number = fields.Char(string='Número de Unidad')

    theoretical_exam_result = fields.Float(
        string='Resultado Examen Teórico',
        help='Ingrese el resultado del examen teórico (0 a 10)',
    )

    @api.constrains('theoretical_exam_result')
    def _check_theoretical_exam_result(self):
        for record in self:
            if record.theoretical_exam_result is not None:
                if record.theoretical_exam_result < 0 or record.theoretical_exam_result > 100:
                    raise ValidationError('El resultado del examen teórico debe estar entre 0 y 100.')


    # === EVALUACIÓN PRUEBA DE MANEJO ===
    # 1. CONOCIMIENTO, INSPECCIÓN Y ADAPTACIÓN DEL VEHÍCULO (5 factores)
    fluid_levels_inspection = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Inspección de los niveles (refrigerante, líquido de frenos, aceite)')

    battery_inspection = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Inspección de estado físico de la batería')

    tire_verification = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Verificación estado de llantas (Estado y presión)')

    safety_adaptation = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Adaptación o graduación del cinturón de seguridad, espejos laterales, asiento y retrovisor')

    lights_verification = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Verificación del estado de las luces (altas, bajas, direccionales, freno de parqueo)')

    # Promedio del Aspecto 1
    knowledge_average = fields.Float(
        string='Promedio Conocimiento e Inspección',
        compute='_compute_knowledge_average',
        store=True,
        digits=(3, 2)
    )

    # Suma del Aspecto 1
    knowledge_sum = fields.Integer(
        string='Suma Conocimiento e Inspección',
        compute='_compute_knowledge_average',
        store=True
    )

    # 2. DESTREZA Y HABILIDADES EN EL MANEJO (10 factores)
    ignition_maneuver = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Maniobra de encendido y arranque del vehículo')

    starting_movement = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Puesta en marcha en plano y en pendiente')

    straight_line_advance = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Avance en línea recta y con ángulos')

    maneuver_coordination = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Coordinación de maniobras: aceleración, freno, cambio y embrague')

    gear_application = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Aplicación de cambios ascendentes y descendentes')

    inclined_terrain = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Descenso y ascenso en terreno inclinado')

    circulation_overtaking = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Maniobra de circulación y adelantamiento')

    clutch_application = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Aplicación del embrague')

    brake_parking = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Aplicación de frenos y parqueo en reversa')

    parking_entry = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Ingreso al área de parqueo en reversa')

    # Promedio del Aspecto 2
    skills_average = fields.Float(
        string='Promedio Destreza y Habilidades',
        compute='_compute_skills_average',
        store=True,
        digits=(3, 2)
    )

    # Suma del Aspecto 2
    skills_sum = fields.Integer(
        string='Suma Destreza y Habilidades',
        compute='_compute_skills_average',
        store=True
    )

    # 3. COMPORTAMIENTO DEL CONDUCTOR FRENTE AL TRÁNSITO (5 factores)
    regulation_employment = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Empleo del reglamento de tránsito (señalizaciones y límites de velocidad)')

    following_distance = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Distancia de seguimiento de parada y lateral')

    lane_changes = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Cambios de carril, de calzada y adelantamientos')

    lane_use = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Uso adecuado de cambio de carriles')

    directional_handling = fields.Selection([
        ('1', '1 - Deficiente'),
        ('2', '2 - Malo'),
        ('3', '3 - Regular'),
        ('4', '4 - Bueno'),
        ('5', '5 - Excelente')
    ], string='Manejo adecuado de las luces direccionales')

    # Promedio del Aspecto 3
    behavior_average = fields.Float(
        string='Promedio Comportamiento en Tránsito',
        compute='_compute_behavior_average',
        store=True,
        digits=(3, 2)
    )

    # Suma del Aspecto 3
    behavior_sum = fields.Integer(
        string='Suma Comportamiento en Tránsito',
        compute='_compute_behavior_average',
        store=True
    )

    # PROMEDIO FINAL
    final_test_average = fields.Float(
        string='Calificación Final de la Prueba',
        compute='_compute_final_test_average',
        store=True,
        digits=(3, 2)
    )
    
    # RESULTADO EXAMEN TEÓRICO (10%)
    theoretical_exam_result_10 = fields.Float(
        string='Resultado Examen Teórico (10%)',
        compute='_compute_theoretical_exam_result_10',
        store=True,
        digits=(3, 2)
    )

    # RESULTADO EXAMEN PRÁCTICO
    practical_exam_result = fields.Float(
        string='Resultado Examen Práctico (90%)',
        compute='_compute_practical_exam_result',
        store=True,
        digits=(3, 2)
    )

    final_test_result = fields.Selection([
        ('not_evaluated', 'No Evaluado'),
        ('failed', 'Reprobado'),
        ('passed', 'Aprobado')
    ], string='Resultado Final', compute='_compute_final_test_result', store=True)

    @api.depends('fluid_levels_inspection', 'battery_inspection', 'tire_verification', 'safety_adaptation', 'lights_verification')
    def _compute_knowledge_average(self):
        for record in self:
            factors = [
                record.fluid_levels_inspection,
                record.battery_inspection,
                record.tire_verification,
                record.safety_adaptation,
                record.lights_verification
            ]
            
            # Filtrar solo los que tienen valor
            numeric_values = [int(factor) for factor in factors if factor]
            
            if numeric_values:
                # Calcular suma
                record.knowledge_sum = sum(numeric_values)
                
                # Calcular promedio con nueva fórmula: (suma_total * valor_seccion) / suma_maxima_posible
                # Para sección 1: (suma * 10) / 25
                # Donde 25 = 5 factores * 5 puntos máximo por factor
                record.knowledge_average = (record.knowledge_sum * 10) / 25
            else:
                record.knowledge_sum = 0
                record.knowledge_average = 0.0

    @api.depends('ignition_maneuver', 'starting_movement', 'straight_line_advance', 'maneuver_coordination', 
                'gear_application', 'inclined_terrain', 'circulation_overtaking', 
                'clutch_application', 'brake_parking', 'parking_entry')
    def _compute_skills_average(self):
        for record in self:
            factors = [
                record.ignition_maneuver,
                record.starting_movement,
                record.straight_line_advance,
                record.maneuver_coordination,
                record.gear_application,
                record.inclined_terrain,
                record.circulation_overtaking,
                record.clutch_application,
                record.brake_parking,
                record.parking_entry
            ]
            
            # Filtrar solo los que tienen valor
            numeric_values = [int(factor) for factor in factors if factor]
            
            if numeric_values:
                # Calcular suma
                record.skills_sum = sum(numeric_values)
                
                # Calcular promedio con nueva fórmula: (suma * 70) / máximo posible
                # Para sección 2: (suma * 70) / 50
                # Donde 50 = 10 factores * 5 puntos máximo por factor
                record.skills_average = (record.skills_sum * 70) / 50
            else:
                record.skills_sum = 0
                record.skills_average = 0.0

    @api.depends('regulation_employment', 'following_distance', 'lane_changes', 'lane_use', 'directional_handling')
    def _compute_behavior_average(self):
        for record in self:
            factors = [
                record.regulation_employment,
                record.following_distance,
                record.lane_changes,
                record.lane_use,
                record.directional_handling
            ]
            
            # Filtrar solo los que tienen valor
            numeric_values = [int(factor) for factor in factors if factor]
            
            if numeric_values:
                # Calcular suma
                record.behavior_sum = sum(numeric_values)
                
                # Calcular promedio con nueva fórmula: (suma * 20) / máximo posible
                # Para sección 3: (suma * 20) / 25
                # Donde 25 = 5 factores * 5 puntos máximo por factor
                record.behavior_average = (record.behavior_sum * 20) / 25
            else:
                record.behavior_sum = 0
                record.behavior_average = 0.0

    @api.depends('theoretical_exam_result')
    def _compute_theoretical_exam_result_10(self):
        for record in self:
            if record.theoretical_exam_result:
                # Calcular el 10% del resultado teórico
                record.theoretical_exam_result_10 = (record.theoretical_exam_result * 10) / 100
            else:
                record.theoretical_exam_result_10 = 0.0

    @api.depends('theoretical_exam_result_10', 'practical_exam_result')
    def _compute_final_test_average(self):
        for record in self:
            # La calificación final es la suma del examen teórico (10%) + examen práctico (90%)
            theoretical_score_10 = record.theoretical_exam_result_10
            practical_score = record.practical_exam_result
            
            # Suma: teórico (10%) + práctico (90%)
            record.final_test_average = theoretical_score_10 + practical_score

    @api.depends('knowledge_average', 'skills_average', 'behavior_average')
    def _compute_practical_exam_result(self):
        for record in self:
            # Calcular la suma de los promedios de cada sección
            sum_of_averages = record.knowledge_average + record.skills_average + record.behavior_average
            
            # Aplicar la fórmula: (suma de promedios * 90) / 100
            if sum_of_averages > 0:
                record.practical_exam_result = (sum_of_averages * 90) / 100
            else:
                record.practical_exam_result = 0.0

    @api.depends('final_test_average')
    def _compute_final_test_result(self):
        for record in self:
            if record.final_test_average == 0:
                record.final_test_result = 'not_evaluated'
            elif record.final_test_average >= 70.0:  # 70 puntos o más para aprobar
                record.final_test_result = 'passed'
            else:
                record.final_test_result = 'failed'

    @api.depends('evaluator_id')
    def _compute_evaluator_job_title(self):
        for record in self:
            if record.evaluator_id:
                # ✅ OPCIÓN 1: Buscar empleado asociado al usuario
                if record.evaluator_id.employee_id:
                    employee = record.evaluator_id.employee_id
                    record.evaluator_job_title = (
                        employee.job_title or 
                        employee.job_id.name or 
                        'Empleado sin puesto definido'
                    )
                
                # ✅ OPCIÓN 2: Si no hay empleado, buscar por user_id
                else:
                    employee = self.env['hr.employee'].search([
                        ('user_id', '=', record.evaluator_id.id)
                    ], limit=1)
                    
                    if employee:
                        record.evaluator_job_title = (
                            employee.job_title or 
                            employee.job_id.name or 
                            'Empleado sin puesto definido'
                        )
                    else:
                        # ✅ FALLBACK: Usar información del usuario
                        record.evaluator_job_title = f"Usuario: {record.evaluator_id.name}"
            else:
                record.evaluator_job_title = 'No asignado'

    @api.depends('license_type')
    def _compute_license_description(self):
        """Mostrar descripción detallada según el tipo de licencia seleccionado"""
        license_descriptions = {
            'tipo_a': 'Para conducir vehículos particulares, como automóviles.',
            'tipo_b': 'Para transporte público (aunque no se considera de servicio particular).',
            'tipo_c': 'Para conducir motocicletas.',
            'tipo_d': 'Para transporte masivo y autobuses (aunque no es de servicio particular).',
            'tipo_e': 'Para conducir vehículos particulares y de carga de hasta 3.5 toneladas, así como para choferes de servicio particular.',
            'tipo_e_federal': 'Para transporte de materiales y residuos peligrosos (aunque no es de uso particular).',
            'permiso_provisional': 'Para menores de edad (16 a 18 años) que deseen conducir vehículos particulares.',
        }
        
        for record in self:
            record.license_description = license_descriptions.get(record.license_type, '')

    @api.depends('stage_id.sequence')
    def _compute_is_driving_test_editable(self):
        for record in self:
            if record.stage_id:
                # ✅ Buscar la etapa "Prueba de Manejo" para obtener su sequence exacto
                driving_test_stage = self.env['hr.recruitment.stage'].search([
                    ('name', 'ilike', 'prueba de manejo')
                ], limit=1)
                
                if driving_test_stage:
                    # ✅ Solo editable cuando está EXACTAMENTE en "Prueba de Manejo"
                    record.is_driving_test_editable = record.stage_id.sequence == driving_test_stage.sequence
                else:
                    record.is_driving_test_editable = False
            else:
                record.is_driving_test_editable = False

    def action_save_driving_test(self):
        """Guardar la información de prueba de manejo"""
        # ✅ Verificación adicional de seguridad
        if not self.is_driving_test_editable:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Acción no permitida',
                    'message': 'No puede editar la prueba de manejo en esta etapa.',
                    'notificationType': 'warning',
                }
            }
        
        # ✅ Validaciones básicas
        if not self.license_type:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Datos Incompletos',
                    'message': 'Debe seleccionar un tipo de licencia.',
                    'notificationType': 'warning',
                }
            }
        
        # ✅ Asegurar que el evaluador esté asignado
        if not self.evaluator_id:
            self.evaluator_id = self.env.user.id
        
        # ✅ Descargar el PDF del reporte
        return self.env.ref('hr_recruitment_estevez.action_hr_applicant_driving_test_report').report_action(self)
    
    def action_send_theoretical_interview(self):
        """
        Envía la entrevista teórica de prueba de manejo al candidato.
        Busca la encuesta por criterios robustos en lugar de ID directo.
        """
        self.ensure_one()
        
        # ✅ Validación: debe estar en etapa de Prueba de Manejo
        if not self.is_driving_test:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Acción no disponible',
                    'message': 'El candidato debe estar en la etapa "Prueba de Manejo" para enviar la entrevista teórica.',
                    'notificationType': 'warning',
                }
            }
        
        # ✅ Validación: debe tener email
        if not self.email_from:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Email requerido',
                    'message': 'El candidato debe tener un email registrado para enviar la entrevista.',
                    'notificationType': 'warning',
                }
            }
        
        # ✅ Buscar la encuesta usando criterios robustos (no ID directo)
        theoretical_survey = self.env['survey.survey'].search([
            ('title', 'ilike', 'EVALUACIÓN TEÓRICA PRUEBA DE MANEJO'),
            ('survey_type', '=', 'recruitment'),
            ('active', '=', True)
        ], limit=1)
        
        if not theoretical_survey:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Encuesta no encontrada',
                    'message': 'No se encontró la "Evaluación Teórica Prueba de Manejo" activa.',
                    'notificationType': 'danger',
                }
            }
        
        # ✅ Validar la encuesta antes de enviar
        try:
            theoretical_survey.check_validity()
        except Exception as validation_error:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error de validación',
                    'message': f'La encuesta no es válida: {str(validation_error)}',
                    'notificationType': 'danger',
                }
            }
        
        try:
            # ✅ Crear/obtener partner si no existe
            if not self.partner_id:
                if not self.partner_name:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Nombre requerido',
                            'message': 'El candidato debe tener un nombre registrado.',
                            'notificationType': 'warning',
                        }
                    }
                
                self.partner_id = self.env['res.partner'].sudo().create({
                    'is_company': False,
                    'name': self.partner_name,
                    'email': self.email_from,
                    'phone': self.partner_phone,
                    'mobile': self.partner_phone
                })
            
            # ✅ Crear la invitación directamente (sin modal)
            user_input = theoretical_survey._create_answer(
                partner=self.partner_id,
                email=self.email_from,
                check_attempts=False  # Permitir múltiples intentos
            )
            
            # ✅ Vincular con el candidato
            user_input.write({
                'applicant_id': self.id,
            })
            
            # ✅ Enviar la invitación por email usando el template estándar
            template = self.env.ref('survey.mail_template_user_input_invite', raise_if_not_found=False)
            if template:
                email_values = {
                    'email_to': self.email_from,
                    'subject': f'Evaluación Teórica - {theoretical_survey.title}',
                }
                template.send_mail(user_input.id, email_values=email_values, force_send=True)
            else:
                # Fallback: crear email simple si no hay template
                survey_url = f"/survey/start/{theoretical_survey.access_token}/{user_input.access_token}"
                mail_values = {
                    'subject': f'Evaluación Teórica - {theoretical_survey.title}',
                    'body_html': f'''
                    <p>Estimado/a {self.partner_name},</p>
                    <p>Se le ha asignado una evaluación teórica como parte del proceso de selección.</p>
                    <p><strong>Enlace de acceso:</strong> <a href="{survey_url}" target="_blank">Hacer la evaluación</a></p>
                    <p><strong>Tiempo límite:</strong> {theoretical_survey.time_limit} minutos</p>
                    <p>Saludos cordiales,<br/>Equipo de Reclutamiento</p>
                    ''',
                    'email_to': self.email_from,
                    'email_from': self.env.user.email or 'noreply@company.com',
                }
                mail = self.env['mail.mail'].create(mail_values)
                mail.send()
            
            # ✅ Registrar en el chatter del candidato
            survey_url = f"/survey/start/{theoretical_survey.access_token}/{user_input.access_token}"
            self.message_post(
                body=f"""
                <p>✅ <strong>Entrevista Teórica Enviada</strong></p>
                <ul>
                    <li><strong>Encuesta:</strong> {theoretical_survey.title}</li>
                    <li><strong>Email:</strong> {self.email_from}</li>
                    <li><strong>Fecha de envío:</strong> {fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Enlace:</strong> <a href="{survey_url}" target="_blank">Acceder a la entrevista</a></li>
                </ul>
                """,
                subject="Entrevista Teórica Enviada"
            )
            
            # ✅ Notificación de éxito
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ Entrevista enviada exitosamente',
                    'message': f'La evaluación teórica ha sido enviada a {self.email_from}',
                    'notificationType': 'success',
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error al enviar',
                    'message': f'Ocurrió un error al enviar la entrevista: {str(e)}',
                    'notificationType': 'danger',
                }
            }
    
    