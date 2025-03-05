from odoo import models, fields, api

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
        existing_docs = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', applicant_id)
        ])

        # Verificar cuáles ya están adjuntos
        docs_data = []
        for doc in required_documents:
            docs_data.append({
                'name': doc,
                'applicant_id': applicant_id,
                'attached': any(doc in d.name for d in existing_docs),
            })

        # Crear los registros
        return self.create(docs_data)
