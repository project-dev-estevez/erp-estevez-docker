from odoo import models, fields, api
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class HrApplicantDocument(models.Model):
    _name = 'hr.applicant.document'
    _description = 'Documentos requeridos para el aplicante'

    name = fields.Char(string="Nombre del Documento", required=True)
    applicant_id = fields.Many2one('hr.applicant', string="Aplicante", required=True)
    attached = fields.Boolean(string="Adjunto", compute="_compute_attached")

    def _normalize_doc_name(self, name):
        normalized = (name or '').strip().lower()
        return ' '.join(normalized.split())

    @api.depends('name', 'applicant_id')
    def _compute_attached(self):
        for record in self:
            # Comparar por nombre normalizado para soportar variaciones de acentos/espacios.
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', record.applicant_id.id),
            ])
            target_name = self._normalize_doc_name(record.name)
            record.attached = any(self._normalize_doc_name(att.name) == target_name for att in attachments)

    def action_attach_document(self):
        self.ensure_one()

        # Buscar y eliminar documentos previos con nombre equivalente normalizado.
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.applicant_id.id),
        ])
        target_name = self._normalize_doc_name(self.name)
        existing_attachment = attachments.filtered(
            lambda att: self._normalize_doc_name(att.name) == target_name
        )
        
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
                'default_name': self.name,
                'force_document_name': True,
            },
        }   

    @api.model
    def create_required_documents(self, applicant_id):
        """ Crea registros temporales de documentos requeridos """
        required_documents = [
            'INE Frente/Reverso',
            #'INE Reverso',
            'Curriculum',
            'Acta de Nacimiento',
            'Comprobante de estudios',
            'Comprobante de domicilio',
            'Comprobante Número de Seguridad Social',
            #'Formato RFC',
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
        normalized_existing = {
            self._normalize_doc_name(doc.name)
            for doc in existing_docs
        }
        docs_data = []
        for doc_name in required_documents:
            attached = self._normalize_doc_name(doc_name) in normalized_existing
            _logger.info(f"Documento: {doc_name}, Adjunto: {attached}")  # Depuración
            docs_data.append({
                'name': doc_name,
                'applicant_id': applicant_id,
                'attached': attached,  # Asignar el valor correcto
            })

        # Crear los registros
        return self.create(docs_data)
    

    def action_view_document(self):
        self.ensure_one()
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.applicant_id.id),
        ], order='write_date desc, id desc')
        target_name = self._normalize_doc_name(self.name)
        attachment = attachments.filtered(
            lambda att: self._normalize_doc_name(att.name) == target_name
        )[:1]
        
        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Vista Previa - {self.name}',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(self.env.ref('hr_recruitment_estevez.view_attachment_image_form').id, 'form')],
            'flags': {'mode': 'readonly'},
        }

    def action_download_document(self):
        """ Descarga el archivo adjunto """
        self.ensure_one()
        # Buscar el archivo adjunto relacionado con este documento
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.applicant_id.id),
        ], order='write_date desc, id desc')
        target_name = self._normalize_doc_name(self.name)
        attachment = attachments.filtered(
            lambda att: self._normalize_doc_name(att.name) == target_name
        )[:1]
        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")
        # Descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }