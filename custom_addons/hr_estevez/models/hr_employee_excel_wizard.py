import io
import xlwt
import base64
from datetime import datetime, date
from odoo import models, fields, _
from odoo.exceptions import UserError

class HrEmployeeExcelWizard(models.TransientModel):
    _name = 'hr.employee.excel.wizard'
    _description = 'Asistente para reporte de empleados en Excel'

    # Campos para selección de empleados
    employee_status = fields.Selection([
        ('active', 'Solo Activos'),
        ('inactive', 'Solo Inactivos'),
        ('all', 'Todos (Activos e Inactivos)')
    ], string='Estado del Empleado', default='active', required=True)

    # Campos para selección de fechas
    date_filter = fields.Selection([
        ('all', 'Todos los tiempos'),
        ('range', 'Rango de fechas')
    ], string='Filtrar por fecha', default='all')
    
    start_date = fields.Date(string='Fecha inicial')
    end_date = fields.Date(string='Fecha final')
    
    # Campos seleccionables para el reporte
    include_names = fields.Boolean(string='Nombres', default=True)
    include_last_name = fields.Boolean(string='Apellido Paterno', default=True)
    include_mother_last_name = fields.Boolean(string='Apellido Materno', default=True)
    include_employee_number = fields.Boolean(string='Número de Empleado', default=True)
    include_job_title = fields.Boolean(string='Puesto', default=True)
    include_department = fields.Boolean(string='Departamento', default=True)
    include_company = fields.Boolean(string='Compañía', default=True)
    include_work_email = fields.Boolean(string='Email Corporativo', default=True)
    include_work_phone = fields.Boolean(string='Teléfono Laboral', default=True)
    include_private_phone = fields.Boolean(string='Teléfono Personal', default=True)
    include_birthday = fields.Boolean(string='Fecha de Nacimiento')
    include_age = fields.Boolean(string='Edad')
    include_gender = fields.Boolean(string='Género')
    include_marital = fields.Boolean(string='Estado Civil')
    include_curp = fields.Boolean(string='CURP')
    include_rfc = fields.Boolean(string='RFC')
    include_nss = fields.Boolean(string='NSS')
    include_infonavit = fields.Boolean(string='Infonavit')
    include_employment_date = fields.Boolean(string='Fecha de Ingreso')
    include_years_service = fields.Boolean(string='Años de Servicio')
    include_payment_type = fields.Boolean(string='Tipo de Pago')
    include_payroll_type = fields.Boolean(string='Tipo de Nómina')
    include_bank = fields.Boolean(string='Banco')
    include_clabe = fields.Boolean(string='CLABE')
    include_active = fields.Boolean(string='Estado (Activo/Inactivo)', default=True)
    include_work_location = fields.Boolean(string='Lugar de Trabajo')
    include_patron = fields.Boolean(string='Patrón')
    include_establecimiento = fields.Boolean(string='Establecimiento')
    include_resource_calendar = fields.Boolean(string='Horario Laboral')
    include_account_number = fields.Boolean(string='Número de Cuenta')
    include_address = fields.Boolean(string='Dirección Laboral')
    include_private_colonia = fields.Boolean(string='Colonia')
    include_municipality = fields.Boolean(string='Municipio')
    include_state = fields.Boolean(string='Estado')
    include_private_street2 = fields.Boolean(string='Numero')
    include_private_zip = fields.Boolean(string='Código Postal')
    include_private_email = fields.Boolean(string='Email Personal')
    include_license_number = fields.Boolean(string='Número de Licencia')
    
    # Campo para archivo generado
    excel_file = fields.Binary(string='Archivo Excel')
    file_name = fields.Char(string='Nombre del archivo')

    def generate_excel_report(self):
        """Generar el reporte en Excel"""
        # Validar rango de fechas si se seleccionó
        if self.date_filter == 'range':
            if not self.start_date or not self.end_date:
                raise UserError(_('Debe seleccionar un rango de fechas válido.'))
            if self.start_date > self.end_date:
                raise UserError(_('La fecha inicial no puede ser mayor a la fecha final.'))
        
        # Crear libro de Excel
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Empleados')
        
        # Estilos - CORREGIDO
        header_style = xlwt.easyxf(
            'font: bold on, height 240; '
            'align: wrap on, vert centre, horiz center; '
            'pattern: pattern solid, fore_colour light_blue; '
            'borders: left thin, right thin, top thin, bottom thin'
        )
        
        data_style = xlwt.easyxf(
            'align: vert centre, horiz left; '
            'borders: left thin, right thin, top thin, bottom thin'
        )
        
        # Estilo para fechas - CORREGIDO
        date_style = xlwt.easyxf(
            'align: vert centre, horiz left; '
            'borders: left thin, right thin, top thin, bottom thin'
        )
        date_style.num_format_str = 'DD/MM/YYYY'
        
        # Estilo para números
        number_style = xlwt.easyxf(
            'align: vert centre, horiz right; '
            'borders: left thin, right thin, top thin, bottom thin'
        )
        number_style.num_format_str = '0'
        
        # Preparar encabezados
        headers = []
        if self.include_names:
            headers.append('Nombres')
        if self.include_last_name:
            headers.append('Apellido Paterno')
        if self.include_mother_last_name:
            headers.append('Apellido Materno')
        if self.include_employee_number:
            headers.append('Número de Empleado')
        if self.include_job_title:
            headers.append('Puesto')
        if self.include_department:
            headers.append('Departamento')
        if self.include_company:
            headers.append('Compañía')
        if self.include_work_email:
            headers.append('Email Corporativo')
        if self.include_work_phone:
            headers.append('Teléfono Laboral')
        if self.include_private_phone:
            headers.append('Teléfono Personal')
        if self.include_birthday:
            headers.append('Fecha de Nacimiento')
        if self.include_age:
            headers.append('Edad')
        if self.include_gender:
            headers.append('Género')
        if self.include_marital:
            headers.append('Estado Civil')
        if self.include_curp:
            headers.append('CURP')
        if self.include_rfc:
            headers.append('RFC')
        if self.include_nss:
            headers.append('NSS')
        if self.include_infonavit:
            headers.append('Infonavit')
        if self.include_employment_date:
            headers.append('Fecha de Ingreso')
        if self.include_years_service:
            headers.append('Años de Servicio')
        if self.include_payment_type:
            headers.append('Tipo de Pago')
        if self.include_payroll_type:
            headers.append('Tipo de Nómina')
        if self.include_bank:
            headers.append('Banco')
        if self.include_clabe:
            headers.append('CLABE')
        if self.include_active:
            headers.append('Estado')
        if self.include_work_location:
            headers.append('Lugar de Trabajo')
        if self.include_patron:
            headers.append('Patrón')
        if self.include_establecimiento:
            headers.append('Establecimiento')
        if self.include_resource_calendar:
            headers.append('Horario Laboral')
        if self.include_account_number:
            headers.append('Número de Cuenta')
        if self.include_address:
            headers.append('Dirección Laboral')
        if self.include_private_colonia:
            headers.append('Colonia')
        if self.include_municipality:
            headers.append('Municipio')
        if self.include_state:
            headers.append('Estado')
        if self.include_private_street2:
            headers.append('Numero')
        if self.include_private_zip:
            headers.append('Código Postal')
        if self.include_private_email:
            headers.append('Email Personal')
        if self.include_license_number:
            headers.append('Número de Licencia')
        
        # Escribir encabezados
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_style)
            # Ajustar ancho de columnas
            worksheet.col(col).width = 256 * 20  # 20 caracteres de ancho
        
        # Filtrar empleados
        domain = []
        
        # Filtrar por estado
        if self.employee_status == 'active':
            domain.append(('active', '=', True))
        elif self.employee_status == 'inactive':
            domain.append(('active', '=', False))
        # Si es 'all', no aplicamos filtro de activo
        
        # Filtrar por rango de fechas (si aplica)
        if self.date_filter == 'range' and self.start_date and self.end_date:
            # Usar campo create_date o otro campo de fecha relevante
            domain.append(('create_date', '>=', self.start_date))
            domain.append(('create_date', '<=', self.end_date))
        
        # Obtener empleados
        employees = self.env['hr.employee'].search(domain, order='employee_number')
        
        if not employees:
            raise UserError(_('No se encontraron empleados con los criterios seleccionados.'))
        
        # Calcular edad si no existe el campo
        today = date.today()
        
        # Escribir datos
        row = 1
        for employee in employees:
            col = 0
            
            if self.include_names:
                worksheet.write(row, col, employee.names or '', data_style)
                col += 1
            
            if self.include_last_name:
                worksheet.write(row, col, employee.last_name or '', data_style)
                col += 1
            
            if self.include_mother_last_name:
                worksheet.write(row, col, employee.mother_last_name or '', data_style)
                col += 1
            
            if self.include_employee_number:
                worksheet.write(row, col, employee.employee_number or '', data_style)
                col += 1
            
            if self.include_job_title:
                worksheet.write(row, col, employee.job_id.name if employee.job_id else '', data_style)
                col += 1
            
            if self.include_department:
                worksheet.write(row, col, employee.department_id.name if employee.department_id else '', data_style)
                col += 1
            
            if self.include_company:
                worksheet.write(row, col, employee.company_id.name if employee.company_id else '', data_style)
                col += 1
            
            if self.include_work_email:
                worksheet.write(row, col, employee.work_email or '', data_style)
                col += 1
            
            if self.include_work_phone:
                worksheet.write(row, col, employee.work_phone or '', data_style)
                col += 1
            
            if self.include_private_phone:
                worksheet.write(row, col, employee.private_phone or '', data_style)
                col += 1
            
            if self.include_birthday:
                if employee.birthday:
                    # Convertir string a datetime para xlwt
                    try:
                        birth_date = fields.Date.from_string(employee.birthday)
                        worksheet.write(row, col, birth_date, date_style)
                    except:
                        worksheet.write(row, col, employee.birthday or '', data_style)
                else:
                    worksheet.write(row, col, '', data_style)
                col += 1
            
            if self.include_age:
                # Calcular edad si no existe el campo age
                age = 0
                if employee.birthday:
                    try:
                        birth_date = fields.Date.from_string(employee.birthday)
                        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    except:
                        age = employee.age or 0
                else:
                    age = employee.age or 0
                worksheet.write(row, col, age, data_style)
                col += 1
            
            if self.include_gender:
                gender_dict = {
                    'male': 'Masculino',
                    'female': 'Femenino',
                    'other': 'Otro'
                }
                worksheet.write(row, col, gender_dict.get(employee.gender, ''), data_style)
                col += 1
            
            if self.include_marital:
                marital_dict = {
                    'single': 'Soltero(a)',
                    'married': 'Casado(a)',
                    'cohabitant': 'Unión libre',
                    'widower': 'Viudo(a)',
                    'divorced': 'Divorciado(a)'
                }
                worksheet.write(row, col, marital_dict.get(employee.marital, ''), data_style)
                col += 1
            
            if self.include_curp:
                worksheet.write(row, col, employee.curp or '', data_style)
                col += 1
            
            if self.include_rfc:
                worksheet.write(row, col, employee.rfc or '', data_style)
                col += 1
            
            if self.include_nss:
                worksheet.write(row, col, employee.nss or '', data_style)
                col += 1
            
            if self.include_infonavit:
                worksheet.write(row, col, 'Sí' if employee.infonavit else 'No', data_style)
                col += 1
            
            if self.include_employment_date:
                if employee.employment_start_date:
                    try:
                        emp_date = fields.Date.from_string(employee.employment_start_date)
                        worksheet.write(row, col, emp_date, date_style)
                    except:
                        worksheet.write(row, col, employee.employment_start_date or '', data_style)
                else:
                    worksheet.write(row, col, '', data_style)
                col += 1
            
            if self.include_years_service:
                worksheet.write(row, col, employee.years_of_service or 0, data_style)
                col += 1
            
            if self.include_payment_type:
                payment_dict = {
                    'weekly': 'Semanal',
                    'biweekly': 'Quincenal'
                }
                worksheet.write(row, col, payment_dict.get(employee.payment_type, ''), data_style)
                col += 1
            
            if self.include_payroll_type:
                payroll_dict = {
                    'cash': 'Efectivo',
                    'mixed': 'Mixto',
                    'imss': 'IMSS'
                }
                worksheet.write(row, col, payroll_dict.get(employee.payroll_type, ''), data_style)
                col += 1
            
            if self.include_bank:
                worksheet.write(row, col, employee.bank_id.name if employee.bank_id else '', data_style)
                col += 1
            
            if self.include_clabe:
                worksheet.write(row, col, employee.clabe or '', data_style)
                col += 1
            
            if self.include_active:
                worksheet.write(row, col, 'Activo' if employee.active else 'Inactivo', data_style)
                col += 1

            if self.include_work_location:
                worksheet.write(row, col, employee.work_location_id.name if employee.work_location_id else '', data_style)
                col += 1

            if self.include_patron:
                worksheet.write(row, col, employee.patron if employee.patron else '', data_style)
                col += 1
            
            if self.include_establecimiento:
                worksheet.write(row, col, employee.establecimiento if employee.establecimiento else '', data_style)
                col += 1

            if self.include_resource_calendar:
                worksheet.write(row, col, employee.resource_calendar_id.name if employee.resource_calendar_id else '', data_style)
                col += 1

            if self.include_account_number:
                worksheet.write(row, col, employee.account_number or '', data_style)
                col += 1

            if self.include_address:
                worksheet.write(row, col, employee.address_id.name if employee.address_id else '', data_style)
                col += 1

            if self.include_private_colonia:
                worksheet.write(row, col, employee.private_colonia or '', data_style)
                col += 1

            if self.include_municipality:
                worksheet.write(row, col, employee.municipality_id.name or '', data_style)
                col += 1

            if self.include_state:
                worksheet.write(row, col, employee.state_id.name or '', data_style)
                col += 1

            if self.include_private_street2:
                worksheet.write(row, col, employee.private_street2 or '', data_style)
                col += 1

            if self.include_private_zip:
                worksheet.write(row, col, employee.private_zip or '', data_style)
                col += 1

            if self.include_private_email:
                worksheet.write(row, col, employee.private_email or '', data_style)
                col += 1

            if self.include_license_number:
                worksheet.write(row, col, employee.license_number or '', data_style)
                col += 1
            
            row += 1
        
        # Guardar en memoria
        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodebytes(fp.read())
        fp.close()
        
        # Actualizar wizard con el archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'reporte_empleados_{timestamp}.xls'
        
        self.write({
            'excel_file': excel_file,
            'file_name': filename
        })
        
        # Devolver acción para mostrar notificación
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    
    def select_all_fields(self):
        """Seleccionar todos los campos"""
        self.write({
            'include_names': True,
            'include_last_name': True,
            'include_mother_last_name': True,
            'include_employee_number': True,
            'include_job_title': True,
            'include_department': True,
            'include_company': True,
            'include_work_email': True,
            'include_work_phone': True,
            'include_private_phone': True,
            'include_birthday': True,
            'include_age': True,
            'include_gender': True,
            'include_marital': True,
            'include_curp': True,
            'include_rfc': True,
            'include_nss': True,
            'include_infonavit': True,
            'include_employment_date': True,
            'include_years_service': True,
            'include_payment_type': True,
            'include_payroll_type': True,
            'include_bank': True,
            'include_clabe': True,
            'include_active': True,
            'include_work_location': True,
            'include_patron': True,
            'include_establecimiento': True,
            'include_resource_calendar': True,
            'include_account_number': True,
            'include_address': True,
            'include_private_colonia': True,
            'include_municipality': True,
            'include_state': True,
            'include_private_street2': True,
            'include_private_zip': True,
            'include_private_email': True,
            'include_license_number': True,
        })
        # Devuelve una acción para recargar el wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def clear_all_fields(self):
        """Deseleccionar todos los campos"""
        self.write({
            'include_names': False,
            'include_last_name': False,
            'include_mother_last_name': False,
            'include_employee_number': False,
            'include_job_title': False,
            'include_department': False,
            'include_company': False,
            'include_work_email': False,
            'include_work_phone': False,
            'include_private_phone': False,
            'include_birthday': False,
            'include_age': False,
            'include_gender': False,
            'include_marital': False,
            'include_curp': False,
            'include_rfc': False,
            'include_nss': False,
            'include_infonavit': False,
            'include_employment_date': False,
            'include_years_service': False,
            'include_payment_type': False,
            'include_payroll_type': False,
            'include_bank': False,
            'include_clabe': False,
            'include_active': False,
            'include_work_location': False,
            'include_patron': False,
            'include_establecimiento': False,
            'include_resource_calendar': False,
            'include_account_number': False,
            'include_address': False,
            'include_private_colonia': False,
            'include_municipality': False,
            'include_state': False,
            'include_private_street2': False,
            'include_private_zip': False,
            'include_private_email': False,
            'include_license_number': False,
        })
        # Devuelve una acción para recargar el wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }