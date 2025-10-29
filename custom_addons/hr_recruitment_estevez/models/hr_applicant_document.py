from odoo import models, fields, api
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class HrApplicantDocument(models.Model):
    _name = 'hr.applicant.document'
    _description = 'Documentos requeridos para el aplicante'

    name = fields.Char(string="Nombre del Documento", required=True)
    applicant_id = fields.Many2one('hr.applicant', string="Aplicante", required=True)
    attached = fields.Boolean(string="Adjunto", compute="_compute_attached", store=True)

    @api.depends('name', 'applicant_id')
    def _compute_attached(self):
        for record in self:
            # Buscar archivos adjuntos relacionados con este documento requerido
            existing_docs = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', record.applicant_id.id),
                ('name', '=', record.name)  # Buscar coincidencias exactas en el nombre del archivo
            ])
            # Actualizar el campo attached
            record.attached = bool(existing_docs)

    def action_attach_document(self):
        self.ensure_one()

        # Buscar y eliminar el documento existente con el mismo nombre
        existing_attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.applicant_id.id),
            ('name', '=', self.name)
        ], limit=1)
        
        if existing_attachment:
            existing_attachment.unlink()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_recruitment_estevez.view_attachment_form_custom').id,
            'target': 'new',
            'name': 'Adjunte el Documento',
            'context': {
                'default_res_model': 'hr.applicant',
                'default_res_id': self.applicant_id.id,
                'default_name': self.name
            },
        }   

    @api.model
    def create_required_documents(self, applicant_id):
        """ Crea registros temporales de documentos requeridos """
        required_documents = [
            'INE Frente/Reverso',
            'INE Reverso',
            'Curriculum',
            'Acta de Nacimiento',
            'Comprobante de estudios',
            'Comprobante de domicilio',
            'Comprobante Número de Seguridad Social',
            'Formato RFC',
            'Licencia de Conducir',
            'Cartas de Recomendacion Laboral',
            'Carta de Recomendacion Personal',
            'Carta de retencion Infonavit',
            'CURP',
            'Prueba Psicométrica',
            'Historia Clínica',
            'Solicitud de empleo',
            'Anexo G - Aviso de Privacidad de Candidatos',
            'Cuestionario de Salud',
            'Constancia de semanas cotizadas en el IMSS',
            'Constancia de situación fiscal (SAT)',
            'Cuenta Bancaria',
            'Carta de retención de FONACOT',
            'Referencias personales/laborales',
            'Evidencia prueba de manejo',
            'Acuse Kit de contratación',
        ]

        # Buscar archivos adjuntos asociados al aplicante
        existing_docs = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', applicant_id)
        ])

        # Verificar cuáles documentos ya están adjuntos
        docs_data = []
        for doc_name in required_documents:
            # Verificar si hay un archivo adjunto con un nombre que coincida
            attached = any(doc_name == doc.name for doc in existing_docs)
            _logger.info(f"Documento: {doc_name}, Adjunto: {attached}")  # Depuración
            docs_data.append({
                'name': doc_name,
                'applicant_id': applicant_id,
                'attached': attached,  # Asignar el valor correcto
            })

        # Crear los registros
        return self.create(docs_data)
    

    def action_view_document(self):
        """ Abre el archivo adjunto en una nueva ventana """
        self.ensure_one()
        # Buscar el archivo adjunto relacionado con este documento
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.applicant_id.id),
            ('name', '=', self.name)
        ], limit=1)
        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")
        # Abrir el archivo en una nueva ventana
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=false',
            'target': 'new',
        }

    def action_download_document(self):
        """ Descarga el archivo adjunto """
        self.ensure_one()
        # Buscar el archivo adjunto relacionado con este documento
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.applicant_id.id),
            ('name', '=', self.name)
        ], limit=1)
        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")
        # Descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }