from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class HrApplicantDocument(models.TransientModel):
    _name = 'hr.applicant.document'
    _description = 'Documentos requeridos para el aplicante'

    name = fields.Char(string="Nombre del Documento", required=True)
    applicant_id = fields.Many2one('hr.applicant', string="Aplicante", required=True)
    attached = fields.Boolean(string="Adjunto", default=False)

    @api.model
    def create_required_documents(self, applicant_id):
        """ Crea registros temporales de documentos requeridos """
        required_documents = [
            'INE Frente',
            'INE Reverso',
            'Curriculum',
            'Acta de Nacimiento',
            'Comprobante de estudios',
            'Comprobante de domicilio',
            'Formato IMSS',
            'Formato RFC',
            'Licencia de Conducir',
            'Cartas de Recomendacion Laboral',
            'Carta de Recomendacion Personal',
            'Carta de retencion Infonavit',
            'CURP',
            'Prueba Psicométrica'
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
            attached = any(doc_name.lower() in doc.name.lower() for doc in existing_docs)
            _logger.info(f"Documento: {doc_name}, Adjunto: {attached}")  # Depuración
            docs_data.append({
                'name': doc_name,
                'applicant_id': applicant_id,
                'attached': attached,  # Asignar el valor correcto
            })

        # Crear los registros
        return self.create(docs_data)