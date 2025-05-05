from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = 'Préstamos y Anticipos'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, ondelete='cascade')
    request_date = fields.Date(string='Fecha de Solicitud del Préstamo', required=True)
    application_date = fields.Date(string='Fecha de Aplicación del Préstamo', required=True)
    start_payment_date = fields.Date(string='Fecha de Inicio de Cobro', required=True)
    requested_amount = fields.Float(string='Monto Solicitado', required=True, help="Ingrese el monto solicitado. Ejemplo: 1000")
    term = fields.Char(string='Plazo', help="Plazo del préstamo o anticipo")
    disbursement_type = fields.Selection([
        ('loan', 'Préstamo'),
        ('advance', 'Anticipo')
    ], string='Tipo de Desembolso', required=True)
    discount_type = fields.Selection([
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal')
    ], string='Tipo de Descuento', required=True)
    concept = fields.Text(string='Concepto', required=True, help="Ingrese el concepto del préstamo o anticipo.")
    discount = fields.Float(string='Descuento', required=True, help="Ingrese el monto del descuento.")

    # Campos calculados
    remaining_balance = fields.Float(string='Saldo Pendiente', compute='_compute_remaining_balance', store=True)
    installments = fields.Char(string='Cuotas', compute='_compute_installments', store=True)

    @api.depends('requested_amount', 'discount')
    def _compute_remaining_balance(self):
        for record in self:
            # Ejemplo: Calcula el saldo pendiente como el monto solicitado menos el descuento acumulado
            record.remaining_balance = record.requested_amount - (record.discount or 0)

    @api.depends('term', 'discount')
    def _compute_installments(self):
        for record in self:
            try:
                # Extraer el número del campo `term` si contiene texto como "24 meses"
                total_installments = int(''.join(filter(str.isdigit, record.term)) or 0)
            except ValueError:
                total_installments = 0

            paid_installments = int(record.requested_amount // record.discount) if record.discount else 0
            record.installments = f"{paid_installments} de {total_installments}" if total_installments else "0 de 0"

    def format_requested_amount(self):
        """Devuelve el monto solicitado con el signo de pesos."""
        self.ensure_one()  # Asegúrate de que solo se procese un regi   stro
        return f"${self.requested_amount:,.2f}"

    def action_save_loan(self):
        """Guarda el préstamo y cierra el modal."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro
        _logger.info("Saving loan record: %s", self)

    def download_loan_report(self):
        """Generates a PDF report for the memorandum."""
        self.ensure_one()  # Ensure only one record is processed
        _logger.info("Downloading memorandum report for record: %s", self)

        return {
            'type': 'ir.actions.report',
            'report_name': 'hr_estevez.report_hr_employee_loan',
            'report_type': 'qweb-pdf',
            'model': self._name,
            'res_id': self.id,
        }
    
    def get_formatted_date(self, date=None):
        """Returns a given date formatted in Spanish. Defaults to today's date if no date is provided."""
        date = date or datetime.today()
        return date.strftime('%d de %B de %Y').upper().replace(
            'JANUARY', 'ENERO').replace('FEBRUARY', 'FEBRERO').replace('MARCH', 'MARZO').replace(
            'APRIL', 'ABRIL').replace('MAY', 'MAYO').replace('JUNE', 'JUNIO').replace(
            'JULY', 'JULIO').replace('AUGUST', 'AGOSTO').replace('SEPTEMBER', 'SEPTIEMBRE').replace(
            'OCTOBER', 'OCTUBRE').replace('NOVEMBER', 'NOVIEMBRE').replace('DECEMBER', 'DICIEMBRE')
    
    # Formateo de monto solicitado a texto
    def format_requested_amount(self):
        """Devuelve el monto solicitado con el signo de pesos."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro
        return f"${self.requested_amount:,.2f}"

    def format_requested_amount_text(self):
        """Convierte el monto solicitado a texto en formato (MIL DOSCIENTOS PESOS 00/100 M.N.)."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro

        def number_to_words(number):
            """Convierte un número entero a palabras en español."""
            units = (
                '', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE'
            )
            teens = (
                'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'
            )
            tens = (
                '', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'
            )
            hundreds = (
                '', 'CIEN', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS',
                'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'
            )

            if number == 0:
                return 'CERO'

            if number < 10:
                return units[number]

            if number < 20:
                return teens[number - 10]

            if number < 100:
                return tens[number // 10] + ('' if number % 10 == 0 else ' Y ' + units[number % 10])

            if number < 1000:
                return hundreds[number // 100] + ('' if number % 100 == 0 else ' ' + number_to_words(number % 100))

            if number < 1000000:
                thousands = number // 1000
                remainder = number % 1000
                if thousands == 1:
                    return 'MIL' + ('' if remainder == 0 else ' ' + number_to_words(remainder))
                else:
                    return number_to_words(thousands) + ' MIL' + ('' if remainder == 0 else ' ' + number_to_words(remainder))

            return str(number)  # Para números mayores, devuelve el número como texto.

        amount = self.requested_amount
        integer_part = int(amount)
        decimal_part = int(round((amount - integer_part) * 100))
        amount_text = number_to_words(integer_part)
        return f"{amount_text} PESOS {decimal_part:02d}/100 M.N."

    def format_requested_amount_full(self):
        """Devuelve el monto solicitado en formato completo: $1,200.00 (MIL DOSCIENTOS PESOS 00/100 M.N.)."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro
        formatted_amount = self.format_requested_amount()  # Ejemplo: $1,200.00
        amount_text = self.format_requested_amount_text()  # Ejemplo: MIL DOSCIENTOS PESOS 00/100 M.N.
        return f"{formatted_amount} ({amount_text})"
    
    def format_amount_per_term(self):
        """Calcula y devuelve el monto por plazo en formato completo: $400.00 (CUATROCIENTOS PESOS 00/100 M.N.)."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro

        # Extraer el número del campo `term` (por ejemplo, "24 meses" -> 24)
        try:
            total_terms = int(''.join(filter(str.isdigit, self.term)) or 0)
        except ValueError:
            total_terms = 0

        if total_terms == 0:
            return "PLAZO INVÁLIDO"

        # Calcular el monto por plazo
        amount_per_term = self.requested_amount / total_terms

        # Formatear el monto en texto
        integer_part = int(amount_per_term)
        decimal_part = int(round((amount_per_term - integer_part) * 100))

        def number_to_words(number):
            """Convierte un número entero a palabras en español."""
            units = (
                '', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE'
            )
            teens = (
                'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'
            )
            tens = (
                '', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'
            )
            hundreds = (
                '', 'CIEN', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS',
                'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'
            )

            if number == 0:
                return 'CERO'

            if number < 10:
                return units[number]

            if number < 20:
                return teens[number - 10]

            if number < 100:
                return tens[number // 10] + ('' if number % 10 == 0 else ' Y ' + units[number % 10])

            if number < 1000:
                return hundreds[number // 100] + ('' if number % 100 == 0 else ' ' + number_to_words(number % 100))

            if number < 1000000:
                thousands = number // 1000
                remainder = number % 1000
                if thousands == 1:
                    return 'MIL' + ('' if remainder == 0 else ' ' + number_to_words(remainder))
                else:
                    return number_to_words(thousands) + ' MIL' + ('' if remainder == 0 else ' ' + number_to_words(remainder))

            return str(number)  # Para números mayores, devuelve el número como texto.

        amount_text = number_to_words(integer_part)
        return f"${amount_per_term:,.2f} ({amount_text} PESOS {decimal_part:02d}/100 M.N.)"
    
    def get_employee_bank_account(self):
        """Obtiene la cuenta bancaria del contrato en curso del empleado."""
        self.ensure_one()  # Asegúrate de que solo se procese un registro
        contract = self.employee_id.contract_id  # Obtiene el contrato actual del empleado
        if contract and contract.state == 'open':  # Verifica que el contrato esté en curso
            return contract.bank_account or "SIN CUENTA ASIGNADA"
        return "SIN CONTRATO ACTIVO"