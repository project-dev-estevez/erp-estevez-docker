from odoo import models, fields, api

class EmployeeElearningReport(models.Model):
    _name = 'employee.elearning.report'
    _description = 'Reporte Integrado Empleados - Cursos Elearning'

    # Campos básicos
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    course_id = fields.Many2one('slide.channel', string='Clave Curso', required=True)
    
    # Campos de display del empleado    
    curp = fields.Char(string='CURP')
    employee_name = fields.Char(string='Nombre')
    primer_apellido = fields.Char(string='Primer Apellido')
    segundo_apellido = fields.Char(string='Segundo Apellido')
    state_key = fields.Char(string='Clave Estado')
    municipality_key = fields.Char(string='Clave Municipio')
    occupation_key = fields.Char(string='Clave Ocupación')
    estudios_key = fields.Char(string='Clave Nivel Estudios')
    documento_key = fields.Char(string='Clave Doc Probatorio')
    institucion_key = fields.Char(string='Clave Institución')
    tematica_key = fields.Char(string='Clave Area Tematica')
    company_id = fields.Many2one('res.company', string='Compañía')
    establecimiento = fields.Selection([
        ('estevezjor', 'Estevez.Jor Servicios'),
        ('herrajes', 'Herrajes Estevez'),
        ('grupo_back', 'Grupo BackBone'),
        ('kuali', 'Kuali Digital'),
        ('makili', 'Makili'),
        ('vigiliner', 'Vigiliner')                
    ], string='Establecimiento')

    # Campos de display del curso
    course_name = fields.Char(string='Nombre Curso')
    clave_curso = fields.Char(string='Clave Curso')
    clave_area_tematica = fields.Char(string='Clave Área Temática')
    duracion = fields.Float(string='Duración')
    fecha_inicio = fields.Date(string='Fecha Inicio')
    fecha_termino = fields.Date(string='Fecha Término')
    clave_tipo_agente = fields.Char(string='Clave Tip Agente')
    clave_modalidad = fields.Char(string='Clave Modalidad')
    clave_capacitacion = fields.Char(string='Clave Capacitación')

    # Campos adicionales de la relación
    date_completed = fields.Date(string="Fecha de finalización")
    score = fields.Float(string="Calificación")
    completion = fields.Float(string="Porcentaje Completado")
    channel_type = fields.Char(string="Tipo de Canal")
    modalidad = fields.Char(string="Modalidad")

    # =============================================
    # MÉTODOS DE SINCRONIZACIÓN AUTOMÁTICA - CORREGIDOS
    # =============================================

    @api.model
    def init(self):
        """Sincronización automática al instalar/actualizar el módulo"""
        print("🔄 Iniciando sincronización automática desde slide.channel.partner...")
        # Comentamos temporalmente para evitar errores en actualización
        # self.populate_report_data()
        pass

    def _get_employee_courses_from_system(self):
        """Obtener las relaciones REALES desde slide.channel.partner - CORREGIDO"""
        relations = []
        
        # Buscar todas las relaciones en slide.channel.partner
        channel_partners = self.env['slide.channel.partner'].search([])
        
        for cp in channel_partners:
            # ENFOQUE SIMPLIFICADO Y SEGURO: Buscar empleado solo por user_id.partner_id
            employee = self.env['hr.employee'].search([
                ('user_id.partner_id', '=', cp.partner_id.id)
            ], limit=1)
            
            # Si no encontramos por user_id, intentamos buscar por work_contact_id
            if not employee:
                employee = self.env['hr.employee'].search([
                    ('work_contact_id', '=', cp.partner_id.id)
                ], limit=1)
            
            if employee and cp.channel_id:
                relations.append({
                    'employee_id': employee.id,
                    'course_id': cp.channel_id.id,
                    'date_completed': cp.completed_date,
                    'completion': cp.completion,
                    'channel_type': cp.channel_id.channel_type,
                    'modalidad': getattr(cp.channel_id, 'modalidad', 'Presencial'),
                })
        
        return relations

    def populate_report_data(self):
        """Poblar la tabla con las relaciones REALES del sistema - CORREGIDO"""
        print("🔄 Buscando relaciones empleado-curso en slide.channel.partner...")
        
        try:
            # Obtener relaciones reales
            real_relations = self._get_employee_courses_from_system()
            
            if not real_relations:
                print("❌ No se encontraron relaciones en slide.channel.partner")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Información',
                        'message': 'No se encontraron relaciones empleado-curso en el sistema',
                        'type': 'warning',
                    }
                }
            
            created_count = 0
            updated_count = 0
            
            for rel_data in real_relations:
                if not rel_data.get('employee_id') or not rel_data.get('course_id'):
                    continue
                    
                # Verificar si ya existe en nuestro reporte
                existing = self.search([
                    ('employee_id', '=', rel_data['employee_id']),
                    ('course_id', '=', rel_data['course_id'])
                ])
                
                if not existing:
                    # Crear registro en nuestro reporte
                    self.create({
                        'employee_id': rel_data['employee_id'],
                        'course_id': rel_data['course_id'],
                        'date_completed': rel_data.get('date_completed'),
                        'completion': rel_data.get('completion', 0),
                        'channel_type': rel_data.get('channel_type', ''),
                        'modalidad': rel_data.get('modalidad', ''),
                    })
                    created_count += 1
                else:
                    # Actualizar registro existente
                    existing.write({
                        'date_completed': rel_data.get('date_completed', existing.date_completed),
                        'completion': rel_data.get('completion', existing.completion),
                        'channel_type': rel_data.get('channel_type', existing.channel_type),
                        'modalidad': rel_data.get('modalidad', existing.modalidad),
                    })
                    updated_count += 1
            
            print(f"✅ Sincronización completada: {created_count} nuevos, {updated_count} actualizados")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sincronización Completada',
                    'message': f'Se sincronizaron {created_count} nuevas relaciones y se actualizaron {updated_count} existentes',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            print(f"❌ Error durante la sincronización: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Error durante la sincronización: {str(e)}',
                    'type': 'danger',
                }
            }

    @api.model
    def create(self, vals):
        """Crear registro manteniendo campos actualizados"""
        record = super().create(vals)
        record._update_display_fields()
        return record

    def write(self, vals):
        """Actualizar registro manteniendo campos actualizados"""
        result = super().write(vals)
        if any(field in vals for field in ['employee_id', 'course_id']):
            self._update_display_fields()
        return result

    def _update_display_fields(self):
        """Actualiza todos los campos relacionados"""
        for record in self:
            # Actualizar datos del empleado
            if record.employee_id:
                record.employee_name = record.employee_id.names
                record.curp = record.employee_id.curp
                record.primer_apellido = record.employee_id.last_name
                record.segundo_apellido = record.employee_id.mother_last_name
                record.state_key = record.employee_id.state_key
                record.municipality_key = record.employee_id.municipality_key
                record.occupation_key = record.employee_id.occupation_key
                record.estudios_key = record.employee_id.estudios_key
                record.institucion_key = record.employee_id.institucion_key
                record.documento_key = record.employee_id.documento_key
                record.company_id = record.employee_id.company_id.id
                record.establecimiento = record.employee_id.establecimiento

            # Actualizar datos del curso
            if record.course_id:
                record.course_name = record.course_id.name
                record.tematica_key = record.course_id.area_tematica.name if record.course_id.area_tematica else ''
                # Agregar aquí los campos específicos de tu modelo slide.channel
                record.clave_curso = getattr(record.course_id, 'clave_curso', '')
                #record.tematica_key = getattr(record.course_id, 'clave_area_tematica', '')
                record.duracion = getattr(record.course_id, 'duracion', 0)
                record.fecha_inicio = getattr(record.course_id, 'fecha_inicio', False)
                record.fecha_termino = getattr(record.course_id, 'fecha_termino', False)
                record.clave_tipo_agente = getattr(record.course_id, 'clave_tipo_agente', '')
                record.clave_modalidad = getattr(record.course_id, 'clave_modalidad', '')
                record.clave_capacitacion = getattr(record.course_id, 'clave_capacitacion', '')

    # =============================================
    # MÉTODOS PARA SINCRONIZACIÓN AUTOMÁTICA FUTURA
    # =============================================

    @api.model
    def sync_with_slide_channel_partner(self):
        """Método para sincronización manual"""
        return self.populate_report_data()

    @api.model
    def _cron_auto_sync(self):
        """Cron para sincronización automática diaria"""
        self.sync_with_slide_channel_partner()

    def debug_employee_relations(self):
        """Método de diagnóstico para verificar las relaciones"""
        print("🔍 Iniciando diagnóstico de relaciones...")
        
        # Verificar slide.channel.partner
        channel_partners = self.env['slide.channel.partner'].search([], limit=5)
        print(f"📊 Ejemplos de slide.channel.partner ({len(channel_partners)} encontrados):")
        
        for cp in channel_partners:
            print(f"   - Partner: {cp.partner_id.name} (ID: {cp.partner_id.id})")
            
            # Intentar diferentes formas de encontrar el empleado
            employee_via_user = self.env['hr.employee'].search([
                ('user_id.partner_id', '=', cp.partner_id.id)
            ], limit=1)
            
            employee_via_contact = self.env['hr.employee'].search([
                ('work_contact_id', '=', cp.partner_id.id)
            ], limit=1)
            
            if employee_via_user:
                print(f"     👤 Empleado encontrado vía user: {employee_via_user.name}")
            elif employee_via_contact:
                print(f"     👤 Empleado encontrado vía work_contact: {employee_via_contact.name}")
            else:
                print(f"     ❌ No se encontró empleado para partner {cp.partner_id.name}")
        
        return True