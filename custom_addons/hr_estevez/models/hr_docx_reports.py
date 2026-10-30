# -*- coding: utf-8 -*-
"""
DOCX report generation for HR documents.
Business logic stays in hr_employee.py / hr_contract.py.
All DOCX rendering is isolated here.
"""
import io
import base64
import logging
import zipfile
from datetime import date, datetime
from xml.sax.saxutils import escape as xml_escape
from PIL import Image, ImageDraw, ImageOps

from docx import Document
from docx.shared import Inches, Pt, Twips
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls, qn
from docx.oxml import OxmlElement, parse_xml

from odoo import fields, models
from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)

J = WD_ALIGN_PARAGRAPH.JUSTIFY
C = WD_ALIGN_PARAGRAPH.CENTER
R = WD_ALIGN_PARAGRAPH.RIGHT

# ---------------------------------------------------------------------------
# Utility builder — no Odoo dependencies
# ---------------------------------------------------------------------------

class _DocxBuilder:

    MESES_ES = {
        1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
        5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
        9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE',
    }

    @classmethod
    def fmt_date(cls, d, sep=' DE '):
        if not d:
            return 'N/A'
        return f"{d.day:02d}{sep}{cls.MESES_ES[d.month]}{sep}{d.year}"

    @classmethod
    def fmt_today(cls):
        return cls.fmt_date(date.today())

    @classmethod
    def emp_address(cls, emp):
        parts = [
            emp.private_street or '',
            (' ' + emp.private_street2) if emp.private_street2 else '',
            (', ' + emp.private_colonia) if emp.private_colonia else '',
            (', ' + emp.private_city) if emp.private_city else '',
            (', ' + emp.private_state_id.name) if emp.private_state_id else '',
            (', C.P. ' + emp.private_zip) if emp.private_zip else '',
        ]
        return ''.join(parts).strip(', ') or 'N/A'

    @classmethod
    def company_address(cls, company):
        p = company.partner_id
        parts = [
            p.street or '',
            (', ' + p.street2) if p.street2 else '',
            (', ' + p.city) if p.city else '',
            (', ' + p.state_id.name) if p.state_id else '',
            (', C.P. ' + p.zip) if p.zip else '',
        ]
        return ''.join(parts).strip(', ') or 'N/A'

    @classmethod
    def entry_date_str(cls, employee):
        contracts = employee.contract_ids.filtered('date_of_entry')
        if not contracts:
            return 'N/A'
        return cls.fmt_date(contracts.sorted('date_of_entry')[0].date_of_entry)

    @staticmethod
    def remove_borders(table):
        tblPr = table._tbl.tblPr if table._tbl.tblPr is not None else OxmlElement('w:tblPr')
        tblBorders = OxmlElement('w:tblBorders')
        for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            el = OxmlElement(f'w:{side}')
            el.set(qn('w:val'), 'none')
            tblBorders.append(el)
        tblPr.append(tblBorders)

    @staticmethod
    def cell(cell, text, bold=False):
        para = cell.paragraphs[0]
        para.alignment = C
        run = para.add_run(str(text) if text else 'N/A')
        run.bold = bold

    @staticmethod
    def cell_left(cell, text, bold=False):
        run = cell.paragraphs[0].add_run(str(text) if text else 'N/A')
        run.bold = bold

    @staticmethod
    def add_cell_bottom_border(cell, size=6, color='000000'):
      tc = cell._tc
      tc_pr = tc.get_or_add_tcPr()
      tc_borders = tc_pr.find(qn('w:tcBorders'))
      if tc_borders is None:
        tc_borders = OxmlElement('w:tcBorders')
        tc_pr.append(tc_borders)
      bottom = tc_borders.find(qn('w:bottom'))
      if bottom is None:
        bottom = OxmlElement('w:bottom')
        tc_borders.append(bottom)
      bottom.set(qn('w:val'), 'single')
      bottom.set(qn('w:sz'), str(size))
      bottom.set(qn('w:space'), '0')
      bottom.set(qn('w:color'), color)

    @staticmethod
    def add_cell_right_border(cell, size=6, color='000000'):
      tc = cell._tc
      tc_pr = tc.get_or_add_tcPr()
      tc_borders = tc_pr.find(qn('w:tcBorders'))
      if tc_borders is None:
        tc_borders = OxmlElement('w:tcBorders')
        tc_pr.append(tc_borders)
      right = tc_borders.find(qn('w:right'))
      if right is None:
        right = OxmlElement('w:right')
        tc_borders.append(right)
      right.set(qn('w:val'), 'single')
      right.set(qn('w:sz'), str(size))
      right.set(qn('w:space'), '0')
      right.set(qn('w:color'), color)

    @staticmethod
    def p(doc, runs, align=J, space_before=0, space_after=None,
          left_indent=0, first_line_indent=0):
        """Add a paragraph with mixed bold/normal runs.
        runs: list of (text, bold) tuples.
        """
        para = doc.add_paragraph()
        para.alignment = align
        if left_indent:
            para.paragraph_format.left_indent = Pt(left_indent)
        if first_line_indent:
            para.paragraph_format.first_line_indent = Pt(first_line_indent)
        if space_before:
            para.paragraph_format.space_before = Pt(space_before)
        if space_after is not None:
            para.paragraph_format.space_after = Pt(space_after)
        for text, bold in runs:
            r = para.add_run(str(text) if text else '')
            r.bold = bold
        return para

    @staticmethod
    def heading(doc, text, underline=False, space_before=8):
        para = doc.add_paragraph()
        para.alignment = C
        para.paragraph_format.space_before = Pt(space_before)
        run = para.add_run(text)
        run.bold = True
        if underline:
            run.underline = True
        return para

    @staticmethod
    def sig_table(doc, left_lines, right_lines, space_pt=56):
        """Two-column signature block."""
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(space_pt)
        tbl = doc.add_table(rows=1, cols=2)
        _DocxBuilder.remove_borders(tbl)
        for cell_obj, lines in ((tbl.rows[0].cells[0], left_lines),
                                (tbl.rows[0].cells[1], right_lines)):
            for i, (text, bold) in enumerate(lines):
                para = cell_obj.paragraphs[0] if i == 0 else cell_obj.add_paragraph()
                para.alignment = C
                run = para.add_run(str(text) if text else '')
                run.bold = bold
        return tbl

    @staticmethod
    def to_bytes(doc):
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    @staticmethod
    def apply_default_typography(doc):
      """Apply a consistent base typography across all DOCX reports."""
      normal = doc.styles['Normal']
      normal.font.name = 'Times New Roman'
      normal.font.size = Pt(12)
      normal.paragraph_format.space_before = Pt(0)
      normal.paragraph_format.space_after = Pt(2)
      normal.paragraph_format.line_spacing = 1.15

    @staticmethod
    def circular_image_bytes(image_b64, size=320):
        """Return a circular PNG without zoom-cropping the original image."""
        img = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert('RGBA')

        # Keep the full image visible by fitting inside the square canvas.
        fitted = ImageOps.contain(img, (size, size), method=Image.Resampling.LANCZOS)
        x = (size - fitted.width) // 2
        y = (size - fitted.height) // 2

        canvas = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        canvas.paste(fitted, (x, y), fitted)

        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)

        out = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        out.paste(canvas, (0, 0), mask)

        stream = io.BytesIO()
        out.save(stream, format='PNG')
        stream.seek(0)
        return stream

    @staticmethod
    def fill_template(template, values):
        """Copia una plantilla .docx del módulo reemplazando los marcadores {{...}} de word/document.xml."""
        output = io.BytesIO()
        with zipfile.ZipFile(file_path(template)) as source, \
                zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as result:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == 'word/document.xml':
                    xml = data.decode('utf-8')
                    for marker, value in values.items():
                        xml = xml.replace(marker, xml_escape(value or 'N/A'))
                    data = xml.encode('utf-8')
                result.writestr(item, data)
        return output.getvalue()

    @staticmethod
    def download(env, model, rec_id, filename, raw_bytes):
        att = env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(raw_bytes).decode(),
            'res_model': model,
            'res_id': rec_id,
            'mimetype': (
                'application/vnd.openxmlformats-officedocument'
                '.wordprocessingml.document'
            ),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{att.id}?download=true',
            'target': 'new',
        }


# ---------------------------------------------------------------------------
# hr.employee DOCX reports
# ---------------------------------------------------------------------------

class HrEmployeeDocxReports(models.Model):
    _inherit = 'hr.employee'

    # --- Carta Patronal ---

    # Réplica de la carta del sistema anterior: Times New Roman 10 pt, sin negritas
    # (salvo el nombre), membrete de Estevez.Jor como encabezado y pie, tabla de datos
    # de 3 columnas (3000 / 720 / resto twips) sin bordes y bloque de firma centrado.
    CARTA_PATRONAL_HEADER_IMG = 'hr_estevez/static/src/img/carta_patronal_encabezado.png'
    CARTA_PATRONAL_FOOTER_IMG = 'hr_estevez/static/src/img/carta_patronal_pie.png'

    def _carta_patronal_address(self):
        """Domicilio con el formato de la carta anterior: CALLE #NÚMERO, COLONIA CIUDAD, ESTADO C.P. 00000."""
        text = self.private_street or ''
        if self.private_street2:
            text += f' #{self.private_street2}'
        if self.private_colonia:
            text += f', {self.private_colonia}'
        if self.private_city:
            text += f' {self.private_city}'
        if self.private_state_id:
            text += f', {self.private_state_id.name}'
        if self.private_zip:
            text += f' C.P. {self.private_zip}'
        return text.strip(', ').upper() or 'N/A'

    def _carta_patronal_company_address(self):
        """Domicilio de la empresa con la puntuación de la carta anterior: CALLE, COLONIA, CIUDAD, ESTADO. C.P. 00000."""
        partner = self.company_id.partner_id
        parts = [partner.street, partner.street2, partner.city, partner.state_id.name]
        text = ', '.join(part for part in parts if part)
        if partner.zip:
            text += f'. C.P. {partner.zip}.'
        return text.upper() or 'N/A'

    def _carta_patronal_company_name(self):
        # Razón social del patrón (mismas mayúsculas y puntuación que CodeIgniter)
        company = self.company_id
        patron = dict(company._fields['patron'].selection).get(company.patron) if company.patron else False
        return (patron or company.name or 'N/A').upper()

    @staticmethod
    def _carta_patronal_rfc(vat):
        """RFC de persona moral separado como en la carta anterior: ESE 111012 E79."""
        vat = (vat or '').replace(' ', '').upper()
        if len(vat) in (12, 13):
            return f'{vat[:-9]} {vat[-9:-3]} {vat[-3:]}'
        return vat or 'N/A'

    def _carta_patronal_registro(self):
        """Registro patronal del empleado separado como en la carta anterior: C5350000 10 0."""
        code = (self.registro_patronal_id.code or '').replace(' ', '')
        if len(code) == 11:
            return f'{code[:8]} {code[8:10]} {code[10:]}'
        return code or 'N/A'

    def _carta_patronal_photo(self):
        """Foto rectangular 3:4 (recorte centrado), igual que la carta anterior."""
        img = Image.open(io.BytesIO(base64.b64decode(self.image_1920))).convert('RGB')
        img = ImageOps.fit(img, (600, 800), method=Image.Resampling.LANCZOS)
        stream = io.BytesIO()
        img.save(stream, format='JPEG', quality=90)
        stream.seek(0)
        return stream

    @staticmethod
    def _carta_patronal_doc_defaults(doc):
        """Times New Roman 10 pt e interlineado sencillo en docDefaults, como la carta anterior.

        Se define ahí (y no en el estilo Normal) porque Word y otros visores interpretan
        distinto un tamaño puesto en el estilo; así ambas cartas se ven igual en cualquier programa.
        """
        defaults = doc.styles.element.find(qn('w:docDefaults'))
        rpr = defaults.find(qn('w:rPrDefault')).find(qn('w:rPr'))
        fonts = rpr.find(qn('w:rFonts'))
        for attr in list(fonts.attrib):
            del fonts.attrib[attr]
        for attr in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
            fonts.set(qn(attr), 'Times New Roman')
        for tag in ('w:sz', 'w:szCs'):
            el = rpr.find(qn(tag))
            if el is None:
                el = OxmlElement(tag)
                rpr.append(el)
            el.set(qn('w:val'), '20')
        lang = rpr.find(qn('w:lang'))
        if lang is not None:
            for attr in list(lang.attrib):
                del lang.attrib[attr]
            lang.set(qn('w:val'), 'es-MX')
        # Espaciado 0 e interlineado sencillo explícitos: sin esto Word aplica su espaciado
        # por defecto y la carta (igual que la del sistema anterior) se pasaba a una 2.ª hoja
        ppr_default = defaults.find(qn('w:pPrDefault'))
        if ppr_default is not None:
            defaults.remove(ppr_default)
        defaults.append(parse_xml(
            f'<w:pPrDefault {nsdecls("w")}><w:pPr>'
            '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            '</w:pPr></w:pPrDefault>'))

    @staticmethod
    def _carta_patronal_table(doc, widths):
        table = doc.add_table(rows=0, cols=len(widths))
        _DocxBuilder.remove_borders(table)
        tbl_pr = table._tbl.tblPr
        cell_mar = OxmlElement('w:tblCellMar')
        for side in ('top', 'left', 'bottom', 'right'):
            el = OxmlElement(f'w:{side}')
            el.set(qn('w:w'), '0')
            el.set(qn('w:type'), 'dxa')
            cell_mar.append(el)
        tbl_pr.append(cell_mar)
        # Ancho automático como la carta anterior
        table.autofit = True
        for col, width in zip(table.columns, widths):
            col.width = width or Inches(1)
        return table

    @staticmethod
    def _carta_patronal_free_columns(table, widths):
        """Quita el ancho de las columnas marcadas con None (columna libre, como la carta anterior).

        Se hace al final porque python-docx necesita el ancho de cada columna para crear filas.
        """
        for index, width in enumerate(widths):
            if width is not None:
                continue
            table.columns[index]._gridCol.attrib.pop(qn('w:w'), None)
            for row in table.rows:
                tc_pr = row.cells[index]._tc.get_or_add_tcPr()
                tc_w = tc_pr.find(qn('w:tcW'))
                if tc_w is not None:
                    tc_pr.remove(tc_w)

    @staticmethod
    def _carta_patronal_row(table, values, widths, spacing=Pt(0.5), align=None):
        row = table.add_row()
        for cell, value, width in zip(row.cells, values, widths):
            if width is not None:
                cell.width = width
            cell._tc.get_or_add_tcPr().append(OxmlElement('w:noWrap'))
            para = cell.paragraphs[0]
            para.paragraph_format.space_before = spacing
            para.paragraph_format.space_after = spacing
            if align is not None:
                para.alignment = align
            if value:
                para.add_run(value)
        return row

    def action_download_carta_patronal_docx(self):
        self.ensure_one()
        b = _DocxBuilder
        doc = Document()

        self._carta_patronal_doc_defaults(doc)

        section = doc.sections[0]
        section.page_width, section.page_height = Inches(8.5), Inches(11)
        section.top_margin = section.bottom_margin = Pt(50)       # 1000 twips
        section.left_margin = section.right_margin = Inches(1)    # 1440 twips
        section.header_distance = section.footer_distance = Inches(0.5)

        # Membrete: logo y línea azul arriba, domicilio de la empresa abajo
        if self.company_id.patron == 'estevezjor':
            section.header.paragraphs[0].add_run().add_picture(
                file_path(self.CARTA_PATRONAL_HEADER_IMG), width=Pt(470))
            section.footer.paragraphs[0].add_run().add_picture(
                file_path(self.CARTA_PATRONAL_FOOTER_IMG), width=Pt(470))
        elif self.company_id.logo:
            logo = io.BytesIO(base64.b64decode(self.company_id.logo))
            section.header.paragraphs[0].add_run().add_picture(logo, height=Pt(60))

        doc.add_paragraph()
        today = fields.Date.context_today(self)
        b.p(doc, [(f'TLALNEPANTLA DE BAZ A {b.fmt_date(today)}', False)], align=R)
        doc.add_paragraph()

        if self.image_1920:
            try:
                para = doc.add_paragraph()
                para.alignment = R
                para.add_run().add_picture(self._carta_patronal_photo(), width=Pt(80), height=Pt(106.67))
            except Exception:
                _logger.warning("Carta patronal: no se pudo insertar la foto del empleado %s", self.id)

        b.p(doc, [('A QUIEN CORRESPONDA', False)])
        doc.add_paragraph()
        b.p(doc, [('PRESENTE:', False)])
        doc.add_paragraph()
        b.p(doc, [
            ('ME PERMITO INFORMAR A USTED, LOS DATOS QUE TENEMOS REGISTRADOS '
             'EN EL EXPEDIENTE DE EL C. ', False),
            (self.name.upper(), True),
            (' EL CUAL LABORA PARA LA EMPRESA Y CONTAMOS CON LOS SIGUIENTES '
             'DATOS EN NUESTROS REGISTROS:', False),
        ], align=J)
        doc.add_paragraph()

        # Una sola tabla para empleado y empresa, así ambas columnas quedan alineadas
        entry_date = self.employment_start_date or (
            self.contract_ids.filtered('date_of_entry').sorted('date_of_entry')[:1].date_of_entry)
        widths = [Pt(150), Pt(36), None]   # 3000 / 720 twips / resto libre
        table = self._carta_patronal_table(doc, widths)
        rows = [
            ('FECHA DE INGRESO:', b.fmt_date(entry_date, sep='-') if entry_date else 'N/A'),
            ('RFC:', (self.rfc or 'N/A').upper()),
            ('IMSS:', self.nss or 'N/A'),
            ('PUESTO:', (self.job_id.name or 'N/A').upper()),
            ('DOMICILIO PARTICULAR:', self._carta_patronal_address()),
            None,
            ('NOMBRE DE LA EMPRESA:', self._carta_patronal_company_name()),
            ('DOMICILIO DE LA EMPRESA:', self._carta_patronal_company_address()),
            ('RFC:', self._carta_patronal_rfc(self.company_id.vat)),
            ('REGISTRO PATRONAL:', self._carta_patronal_registro()),
        ]
        for row in rows:
            label, value = row or ('', '')
            self._carta_patronal_row(table, [label, '', value], widths)
        self._carta_patronal_free_columns(table, widths)

        doc.add_paragraph()

        # Firma: tabla centrada de 4000 twips con espacio para firmar
        sign_width = [Pt(200)]
        sign = self._carta_patronal_table(doc, sign_width)
        sign.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._carta_patronal_row(sign, ['ATENTAMENTE'], sign_width, spacing=Pt(0), align=C)
        self._carta_patronal_row(sign, [''], sign_width, spacing=Pt(17.5), align=C)
        self._carta_patronal_row(sign, ['DPO RECURSOS HUMANOS'], sign_width, spacing=Pt(0), align=C)

        return b.download(self.env, 'hr.employee', self.id,
                          f'{self.name} - Carta Patronal.docx',
                          b.to_bytes(doc))

    # --- Convenio de Salida ---

    # Datos fijos del convenio tal como los imprimía el sistema anterior.
    _CONVENIO_APODERADO = 'EDWIN GONZALEZ SORIA'
    _CONVENIO_TESTIGOS = ('LUIS ENRIQUE CENTELLA TELLEZ', 'VANESA CAMPOS OSORNO')
    _CONVENIO_DOMICILIO_EMPRESA = (
        'FILIBERTO GOMEZ N°46, CENTRO INDUSTRIAL TLALNEPANTLA, '
        'TLALNEPANTLA DE BAZ, ESTADO DE MÉXICO. C.P. 54030.'
    )
    _CONVENIO_HORARIO = 'LUNES A VIERNES 8:00 A 18:00 Y SÁBADOS 8:00 A 12:00'
    _CONVENIO_CANTIDAD = '$0,000.000 (CERO CERO CERO CERO PESOS 00/100 M.N.)'

    @staticmethod
    def _convenio_setup_document(doc):
        """Replica estilos y página del convenio anterior: Calibri 10 pt en
        docDefaults, sin espaciado entre párrafos, carta y márgenes de 1"."""
        styles = doc.styles.element
        old = styles.find(qn('w:docDefaults'))
        new = parse_xml(
            f'<w:docDefaults {nsdecls("w")}><w:rPrDefault><w:rPr>'
            '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Arial" w:cs="Calibri"/>'
            '<w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/>'
            '<w:lang w:val="es-MX"/>'
            '</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr/></w:pPrDefault>'
            '</w:docDefaults>'
        )
        if old is not None:
            old.addprevious(new)
            styles.remove(old)
        else:
            styles.insert(0, new)
        # Estilo Normal "limpio" (sin tamaño, fuente ni espaciado propios).
        normal = doc.styles['Normal'].element
        for tag in ('w:pPr', 'w:rPr'):
            el = normal.find(qn(tag))
            if el is not None:
                normal.remove(el)

        for sec in doc.sections:
            sec.page_width = Twips(12240)
            sec.page_height = Twips(15840)
            sec.top_margin = Twips(1440)
            sec.right_margin = Twips(1440)
            sec.bottom_margin = Twips(1440)
            sec.left_margin = Twips(1440)
            sec.header_distance = Twips(720)
            sec.footer_distance = Twips(720)
            sec.gutter = Twips(0)

    @staticmethod
    def _convenio_par(doc, runs, align=J):
        """Párrafo sin espaciado propio; runs = [(texto, negrita, subrayado)]."""
        para = doc.add_paragraph()
        para.alignment = align
        for run_def in runs:
            text, bold = run_def[0], run_def[1]
            underline = run_def[2] if len(run_def) > 2 else False
            r = para.add_run(text)
            if bold:
                r.bold = True
            if underline:
                r.underline = True
        return para

    @staticmethod
    def _convenio_cell_par(text, bold=False, align=None, after=10):
        jc = f'<w:jc w:val="{align}"/>' if align else ''
        rpr = '<w:rPr><w:b/><w:bCs/></w:rPr>' if bold else ''
        return (
            f'<w:p><w:pPr>{jc}<w:spacing w:before="10" w:after="{after}"/></w:pPr>'
            f'<w:r>{rpr}<w:t xml:space="preserve">{xml_escape(text or "")}</w:t></w:r></w:p>'
        )

    @classmethod
    def _convenio_condiciones_table(cls, doc, rows):
        """Tabla FECHA DE INGRESO / CATEGORÍA / HORARIO: sangría de 720,
        etiqueta con borde derecho e inferior, valor con borde izquierdo e
        inferior (igual que el documento anterior)."""
        border = '<w:{side} w:val="single" w:sz="5" w:space="0" w:color="000000"/>'
        trs = ''
        for i, (label, value) in enumerate(rows):
            valign = '<w:vAlign w:val="center"/>' if i == 0 else ''
            trs += (
                '<w:tr>'
                '<w:tc><w:tcPr><w:tcW w:w="720" w:type="dxa"/><w:noWrap/></w:tcPr>'
                f'{cls._convenio_cell_par("")}</w:tc>'
                '<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/><w:noWrap/>'
                f'<w:tcBorders>{border.format(side="bottom")}{border.format(side="right")}</w:tcBorders>'
                f'{valign}</w:tcPr>{cls._convenio_cell_par(label, bold=True)}</w:tc>'
                '<w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/><w:noWrap/>'
                f'<w:tcBorders>{border.format(side="left")}{border.format(side="bottom")}</w:tcBorders>'
                f'{valign}</w:tcPr>{cls._convenio_cell_par(value)}</w:tc>'
                '</w:tr>'
            )
        cls._convenio_append_table(doc, (
            f'<w:tbl {nsdecls("w")}><w:tblPr><w:tblW w:w="0" w:type="auto"/>'
            '<w:tblLayout w:type="autofit"/><w:tblCellMar>'
            '<w:top w:w="80" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
            '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/>'
            '</w:tblCellMar></w:tblPr><w:tblGrid><w:gridCol w:w="720"/>'
            '<w:gridCol w:w="3000"/><w:gridCol w:w="5000"/></w:tblGrid>'
            f'{trs}</w:tbl>'
        ))

    @classmethod
    def _convenio_firmas_table(cls, doc, empresa, empleado):
        """Bloque de firmas: tabla 2x4 sin bordes, como el documento anterior."""
        p = cls._convenio_cell_par

        def tc(content, valign=False):
            va = '<w:vAlign w:val="center"/>' if valign else ''
            return (f'<w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/><w:noWrap/>'
                    f'{va}</w:tcPr>{content}</w:tc>')

        t1, t2 = cls._CONVENIO_TESTIGOS
        rows = [
            tc(p(empresa, True, 'center')) + tc(p('EL TRABAJADOR', True, 'center')),
            tc(p('RESPONSABLE DE LA RELACION DE TRABAJO', False, 'center')
               + '<w:p/>'
               + p(f'LIC. {cls._CONVENIO_APODERADO}', True, 'center')
               + p('APODERADO LEGAL.', True, 'center', after=300))
            + tc(p(f'C. {empleado}', False, 'center'), valign=True),
            tc(p('TESTIGO', False, 'center', after=600))
            + tc(p('TESTIGO', False, 'center', after=600)),
            tc(p(t1, False, 'center')) + tc(p(t2, False, 'center')),
        ]
        cls._convenio_append_table(doc, (
            f'<w:tbl {nsdecls("w")}><w:tblPr><w:tblW w:w="10000" w:type="dxa"/>'
            '</w:tblPr><w:tblGrid><w:gridCol w:w="5000"/><w:gridCol w:w="5000"/>'
            '</w:tblGrid>' + ''.join(f'<w:tr>{r}</w:tr>' for r in rows) + '</w:tbl>'
        ))

    @staticmethod
    def _convenio_append_table(doc, tbl_xml):
        body = doc.element.body
        tbl = parse_xml(tbl_xml)
        sect = body.find(qn('w:sectPr'))
        if sect is not None:
            sect.addprevious(tbl)
        else:
            body.append(tbl)

    def _convenio_empresa(self):
        """Razón social como la usaba el sistema anterior (campo patrón)."""
        company = self.company_id
        if company.patron:
            label = dict(company._fields['patron'].selection).get(company.patron)
            if label:
                return label
        return (company.name or '').upper()

    def _convenio_fecha(self, d, sep=' DE '):
        if not d:
            return 'N/A'
        return f"{d.day:02d}{sep}{_DocxBuilder.MESES_ES[d.month]}{sep}{d.year}"

    def _convenio_fecha_ingreso(self):
        d = self.employment_start_date
        if not d:
            contracts = self.contract_ids.filtered('date_of_entry')
            if contracts:
                d = contracts.sorted('date_of_entry')[0].date_of_entry
        return self._convenio_fecha(d, sep='-')

    def _convenio_fecha_terminacion(self, today):
        """Fecha de la última baja registrada; si el último movimiento no es
        una baja, la fecha de hoy (zona horaria del usuario)."""
        last = self.env['hr.employee.history'].search(
            [('employee_id', '=', self.id)], order='date desc, id desc', limit=1)
        if last and last.status == 'baja' and last.date:
            return fields.Datetime.context_timestamp(self, last.date).date()
        return today

    def _convenio_domicilio_empleado(self):
        """CALLE NÚMERO, COLONIA CIUDAD, ESTADO C.P. 00000 (formato anterior)."""
        calle = ' '.join(filter(None, [
            (self.private_street or '').strip(),
            (self.private_street2 or '').strip(),
        ]))
        zona = ' '.join(filter(None, [
            (self.private_colonia or '').strip(),
            (self.private_city or '').strip(),
        ]))
        estado = ' '.join(filter(None, [
            (self.private_state_id.name or '').strip() if self.private_state_id else '',
            f'C.P. {self.private_zip.strip()}' if self.private_zip else '',
        ]))
        return ', '.join(filter(None, [calle, zona, estado])).upper() or 'N/A'

    def action_download_convenio_salida_docx(self):
        self.ensure_one()
        emp = (self.name or '').upper()
        co = self._convenio_empresa()
        apoderado = self._CONVENIO_APODERADO
        t1, t2 = self._CONVENIO_TESTIGOS
        dom_co = self._CONVENIO_DOMICILIO_EMPRESA
        today_d = fields.Date.context_today(self)
        today = self._convenio_fecha(today_d)
        fin = self._convenio_fecha(self._convenio_fecha_terminacion(today_d))
        entry = self._convenio_fecha_ingreso()
        job = (self.job_id.name or self.job_title or 'N/A').upper()
        dom_emp = self._convenio_domicilio_empleado()

        doc = Document()
        self._convenio_setup_document(doc)
        par = lambda runs, align=J: self._convenio_par(doc, runs, align)  # noqa: E731

        par([
            ('CONVENIO QUE CELEBRAN POR UNA PARTE LA EMPRESA ', True),
            (co, True),
            (f', REPRESENTADA POR EL LIC. {apoderado} EN SU CARÁCTER DE '
             'APODERADO LEGAL Y UNICO RESPONSABLE DE LA RELACION LABORAL, EN LO '
             'SUCESIVO “LA EMPRESA” Y POR OTRA EL C. ', True),
            (emp, True),
            (', POR SU PROPIO DERECHO, EN SU CARÁCTER DE TRABAJADOR, EN LO '
             'SUCESIVO “EL TRABAJADOR”, CONFORME A LOS SIGUIENTES, '
             'ANTECEDENTES, DECLARACIONES Y CLAUSULAS.', True),
        ])

        par([('A N T E C E D E N T E S', True, True)], C)
        par([
            ('UNICO. - ', True),
            (f'CON FECHA {entry}, LA EMPRESA {co}, Y EL C. {emp}, CELEBRARON UN '
             'CONTRATO INDIVIDUAL DE TRABAJO CON EL OBJETO DE ESTABLECER Y '
             'REGULAR LA RELACION LABORAL Y LAS CONDICIONES EN QUE SE IBA A '
             'PRESTAR ESTA.', False),
        ])

        par([('D E C L A R A C I O N E S', True, True)], C)
        declaraciones = [
            ('I.- ', f'LA EMPRESA {co}, Y EL C. {emp}, MANIFIESTAN, QUE EN LA '
             'CELEBRACIÓN DEL PRESENTE CONVENIO, RECONOCEN MUTUAMENTE QUE NO HA '
             'EXISTIDO DOLO, MALA FE, ERROR, NI CUALQUIER OTRO VICIO DEL '
             'CONSENTIMIENTO QUE PUDIERA AFECTAR LA VALIDEZ DE ESTE INSTRUMENTO '
             'DE INEXISTENCIA O NULIDAD.'),
            ('II.- ', f'EL C. {emp}, EN SU CARACTER DE TRABAJADOR RECONOCE QUE '
             'EN EL CONTENIDO DEL PRESENTE CONVENIO, NO EXISTE NINGUNA RENUNCIA '
             'A SUS DE DERECHOS LABORALES NI MENOSCABO A ESTOS Y EL CONVENIO LO '
             'CELEBRA POR ASI CONVENIR A SUS INTERESES, POR SU PROPIO DERECHO, '
             'DE MANERA VOLUNTARIA, LIBRE Y ESPONTANEA SIN NINGUN TIPO DE '
             'PRESION, POR LO QUE NO EXISTE NINGUN VICIO DEL CONSENTIMIENTO QUE '
             'PUDIERA AFECTAR LA VALIDEZ DE ESTE CONVENIO DE INEXISTENCIA O '
             'NULIDAD.'),
            ('III.- ', f'LA EMPRESA {co}, Y EL C. {emp}, MANIFIESTAN QUE EN SU '
             'CALIDAD DE TESTIGOS ESTAN PRESENTES EN EL DESARROLLO Y FIRMA DEL '
             f'PRESENTE CONVENIO LA C. {t1}, LA C. {t2}.'),
            ('IV.- ', f'LA EMPRESA {co}, Y EL C. {emp}, MANIFIESTAN QUE EL '
             'PRESENTE CONVENIO LO PACTAN DE ESTA FORMA POR RESULTAR MAS '
             'PRACTICO, YA QUE EN LA EJECUCION DEL MISMO SE REALIZA EN ESTE '
             'ACTO Y DE MANERA INMEDIATA, AHORRANDO EL TIEMPO QUE SE HUBIERA '
             'REQUERIDO PARA GENERAR ESTE TRAMITE ANTE EL CENTRO DE '
             'CONCILIACION LABORAL.'),
            ('V.- ', f'LA EMPRESA {co}, Y EL C. {emp}, SE RECONOCEN '
             'RECÍPROCAMENTE SU PERSONALIDAD Y CAPACIDAD LEGAL PARA CELEBRAR EL '
             'PRESENTE CONVENIO POR LO TANTO SE OBLIGAN EN LOS TÉRMINOS DE LAS '
             'SIGUIENTES: '),
        ]
        for num, text in declaraciones:
            par([(num, True), (text, False)])

        par([('C L Á U S U L A S', True, True)], C)
        par([
            ('PRIMERA.- ', True),
            (f'DECLARAN, LA EMPRESA {co}, Y EL C. {emp}, QUE EN TERMINOS DE LA '
             'FRACCION I DEL ARTICULO 53 DE LA LEY FEDERAL DEL TRABAJO, POR ASI '
             f'CONVENIR A LOS INTERESES DEL C. {emp}, POR MUTUO CONSENTIMIENTO, '
             'MANIFIESTAN Y RATIFICAN SU VOLUNTAD DE DAR POR TERMINADA LA '
             'RELACION LABORAL QUE LOS UNIA MEDIANTE EL CONTRATO INDIVIDUAL DE '
             'TRABAJO MENCIONADO EN EL CAPITULO DE ANTECEDENTES DEL PRESENTE '
             'CONVENIO.', False),
        ])
        par([
            ('SEGUNDA.- ', True),
            (f'DECLARA: EL C. {emp}, QUE POR ASI CONVENIR A SUS INTERESES Y POR '
             'MUTUO CONSENTIMIENTO, ES SU LIBRE VOLUNTAD DAR POR TERMINADA LA '
             f'RELACIÓN LABORAL QUE LO HA UNIDO CON LA EMPRESA {co}, HASTA EL '
             'DÍA ', False),
            (fin, True),
            (', TERMINACIÓN LABORAL QUE HACE CON FUNDAMENTO EN LO DISPUESTO POR '
             'LA FRACCIÓN I DEL ARTÍCULO 53 DE LA LEY FEDERAL DEL TRABAJO.', False),
        ])
        par([
            ('TERCERA.- ', True),
            (f'DECLARA: EL C. {emp}, QUE DURANTE EL TIEMPO QUE LABORÓ PARA LA '
             f'EMPRESA {co}, SIEMPRE RECIBIÓ DE ÉSTA DE MANERA PUNTUAL, EL PAGO '
             'DE LOS SALARIOS ORDINARIOS Y EXTRAORDINARIOS; SIEMPRE SE LE '
             'PAGARON LOS SÉPTIMOS DÍAS, DÍAS FESTIVOS, Y HORAS EXTRAS EN LAS '
             'ESCASAS OCASIONES QUE LOS LABORO, LOS SALARIOS DEVENGADOS, ASÍ '
             'COMO LAS VACACIONES, PRIMA VACACIONAL Y AGUINALDO GENERADOS EN EL '
             'TIEMPO LABORADO, COMO CONSECUENCIA NO SE LE ADEUDA NINGUNA SUMA '
             'POR DICHOS CONCEPTOS NI POR NINGÚN OTRO, Y SE LE HAN PAGADO TODAS '
             'Y CADA UNA DE LAS PRESTACIONES LEGALES Y EXTRALEGALES QUE PUDIERAN '
             'CORRESPONDERLE CONFORME A LA LEY Y A SU CONTRATO DE TRABAJO; QUE '
             'IGUALMENTE NO PADECE ENFERMEDAD PROFESIONAL CON MOTIVO Y/O '
             'DERIVADO Y/O A CONSECUENCIA DE SUS LABORES, NI HA SUFRIDO '
             'ACCIDENTE ALGUNO DE TRABAJO DENTRO DEL DESEMPEÑO DE LAS MISMAS, '
             'POR LO QUE POR ESTOS CONCEPTOS NO TIENE NINGUNA ACCIÓN O DERECHO '
             'QUE RESERVARSE PARA EJERCITARLO CON POSTERIORIDAD.', False),
        ])
        par([
            ('CUARTA.- ', True),
            (f'DECLARA: EL C. {emp} QUE INICIO A PRESTAR SUS SERVICIOS '
             'PERSONALES Y SUBORDINADOS, ÚNICAMENTE Y EXCLUSIVAMENTE PARA LA '
             f'EMPRESA {co}, A QUIEN RECONOCE COMO SU ÚNICO PATRON, EN LOS '
             'TÉRMINOS Y CONDICIONES QUE A CONTINUACIÓN SE MENCIONAN:', False),
        ])

        doc.add_paragraph()
        self._convenio_condiciones_table(doc, [
            ('FECHA DE INGRESO', entry),
            ('CATEGORÍA', job),
            ('HORARIO DE LABORES', self._CONVENIO_HORARIO),
        ])
        doc.add_paragraph()

        par([
            ('QUINTA.- ', True),
            (f'DECLARA LA EMPRESA {co}, POR CONDUCTO DEL LIC. {apoderado}, QUIEN '
             'COMPARECE EN SU CARÁCTER DE APODERADO LEGAL, QUE ESTÁ DE ACUERDO '
             f'CON LO MANIFESTADO POR EL C. {emp}, EN LAS CLÁUSULAS, SEGUNDA, '
             'TERCERA Y CUARTA Y CONSECUENTE CON ELLO EXPRESA SU VOLUNTAD PARA '
             'DAR POR TERMINADA POR MUTUO CONSENTIMIENTO LA RELACIÓN LABORAL '
             f'CON EL C. {emp}, EN TÉRMINOS DE LA FRACCIÓN I DEL ARTÍCULO 53 DE '
             'LA LEY FEDERAL DEL TRABAJO.', False),
        ])
        par([
            ('SEXTA.- ', True),
            (f'DECLARAN, LA EMPRESA {co} Y EL C. {emp}, COMO CONSECUENCIA DE LA '
             'TERMINACIÓN DEL CONTRATO INDIVIDUAL DE TRABAJO MENCIONADO EN EL '
             f'CAPITULO DE ANTECEDENTES DEL PRESENTE CONVENIO, LA EMPRESA {co}, '
             f'POR CONDUCTO DEL LIC. {apoderado}, QUIEN COMPARECE EN SU CARÁCTER '
             'DE APODERADO LEGAL, ENTREGA AL ', False),
            (f'C. {emp}', True),
            (', MEDIANTE TRANSFERENCIA QUE EN COPIA SE ANEXA AL PRESENTE Y QUE '
             'FORMA PARTE INTEGRANTE DE ESTE CONVENIO, LA CANTIDAD DE ', False),
            (f'{self._CONVENIO_CANTIDAD} ', True),
            ('COMO FINIQUITO DE TODAS Y CADA UNA DE LAS PRESTACIONES A QUE TUVO '
             f'DERECHO EL C. {emp}, DURANTE LA RELACIÓN LABORAL QUE SE DA POR '
             'TERMINADA EL DÍA ', False),
            (fin, True),
            ('.', False),
        ])
        par([
            ('EN EL ENTENDIDO DE QUE CON ESA CANTIDAD SE LE CUBREN TOTALMENTE '
             'LAS PRESTACIONES QUE LE CORRESPONDIERON HASTA LA JORNADA NORMAL DE '
             f'LABORES QUE LE CORRESPONDIÓ HASTA EL {fin}, DE ACUERDO CON SU '
             'CONTRATO INDIVIDUAL DE TRABAJO Y LA LEY FEDERAL DEL TRABAJO.', False),
        ])
        par([
            ('SÉPTIMA.- ', True),
            (f'DECLARA: EL C. {emp}, QUE ESTA CONFORME CON LA CANTIDAD Y '
             f'CONCEPTOS CITADOS POR LA EMPRESA {co}, EN LA CLÁUSULA ANTERIOR YA '
             'QUE EN SU OPORTUNIDAD SIEMPRE RECIBIÓ DE MANERA ININTERRUMPIDA EL '
             'PAGO DE LOS SÉPTIMOS DÍAS, DÍAS FESTIVOS, Y HORAS EXTRAS EN LAS '
             'ESCASAS OCASIONES QUE LAS LABORO, LOS SALARIOS DEVENGADOS, ASÍ '
             'COMO LAS VACACIONES, PRIMA VACACIONAL Y AGUINALDO GENERADOS EN EL '
             'TIEMPO LABORADO, COMO CONSECUENCIA NO SE LE ADEUDA NINGUNA SUMA '
             'POR DICHOS CONCEPTOS NI POR NINGÚN OTRO, Y SE LE HAN PAGADO TODAS '
             'Y CADA UNA DE LAS PRESTACIONES LEGALES QUE PUDIERAN '
             'CORRESPONDERLE CONFORME A LA LEY FEDERAL DEL TRABAJO Y A LAS '
             'PACTADAS EN SU CONTRATO INDIVIDUAL DE TRABAJO.', False),
        ])
        par([
            ('OCTAVA.- ', True),
            (f'DECLARA: EL C. {emp}, QUE EL PRESENTE DOCUMENTO NO REPRESENTA '
             'NINGUNA RENUNCIA A SUS DERECHOS O MENOSCABO A ESTOS, POR QUE LOS '
             'DERECHOS QUE GENERO HASTA EL DIA ', False),
            (fin, True),
            (' LE ESTAN SIENDO PAGADOS CONFORME A LA LEY FEDERAL DEL TRABAJO Y A '
             'LAS CONDICIONES PACTADAS EN SU CONTRATO INDIVIDUAL DE TRABAJO, '
             'MOTIVO POR EL CUAL NO SE RESERVA NINGUNA ACCIÓN O DERECHO QUE '
             f'EJERCITAR EN CONTRA DE LA EMPRESA {co}, A QUIEN RECONOCE COMO SU '
             'UNICO PATRON, O DE QUIEN LEGALMENTE REPRESENTE SUS INTERESES, O DE '
             'LOS SOCIOS Y ACCIONISTAS DE LA MISMA, O QUIEN MAS LLEGARA A '
             'RESULTAR SER PATRÓN, PROPIETARIO O RESPONSABLE DE LA FUENTE DE '
             'TRABAJO QUE SE UBICA EN ', False),
            (dom_co, True),
            (', POR NINGÚN CONCEPTO DE TIPO LABORAL, CIVIL, PENAL, '
             'ADMINISTRATIVO O CUALQUIER OTRO, MANIFESTANDO QUE DURANTE EL '
             f'TIEMPO QUE LABORÓ PARA LA EMPRESA {co}, A QUIEN RECONOCE COMO SU '
             'ÚNICO PATRÓN LABORAL, NO SUFRIÓ ENFERMEDAD, ACCIDENTE O RIESGO DE '
             'TRABAJO DERIVADO DEL MISMO Y RECIBIÓ EL BUEN TRATO QUE LE '
             'CORRESPONDIÓ COMO TRABAJADOR DE ESTA ÚLTIMA.', False),
        ])
        par([
            ('NOVENA.- ', True),
            (f'DECLARAN, LA EMPRESA {co} Y EL C. {emp}, PARA EFECTOS DE CUMPLIR '
             'CON LOS REQUISITOS DE VALIDEZ QUE REFIERE EL SEGUNDO PARRAFO DEL '
             'ARTICULO 33 DE LA LEY FEDERAL DEL TRABAJO, QUE LA RELACION '
             'CIRCUNSTANCIADA DE LOS HECHOS QUE MOTIVAN EL PRESENTE CONVENIO '
             'ASI COMO LOS DERECHOS COMPRENDIDOS EN ÉL, SE ENCUENTRAN '
             'EXPRESADOS EN EL CAPITULO DE ANTECEDENTES, DECLARACIONES Y EN '
             'TODAS Y CADA UNA DE LAS CLAUSULAS QUE SE MENCIONAN EN EL CUERPO '
             'DEL PRESENTE CONVENIO; Y POR NO CONTENER RENUNCIA DE DERECHOS O '
             'MENOSCABO A ESTOS, POR ESTAR PACTADO DE MANERA VOLUNTARIA, LIBRE '
             'Y ESPONTANEA SIN NINGUN TIPO DE PRESION, POR QUE NO EXISTE NINGUN '
             'VICIO DEL CONSENTIMIENTO QUE PUDIERA AFECTAR LA VALIDEZ DE ESTE '
             f'CONVENIO DE INEXISTENCIA O NULIDAD, POR QUE EL C. {emp} LO '
             'CELEBRA POR SU PROPIO DERECHO Y POR ASI CONVENIR A SUS INTERESES; '
             f'EN ESTE ACTO LA EMPRESA {co} Y EL C. {emp} LO RATIFICAN EN TODAS '
             'Y CADA UNA DE SUS PARTES.', False),
        ])
        par([
            ('DÉCIMA.- ', True),
            ('SEÑALAN LAS PARTES COMO DOMICILIOS PARA EFECTO DE OIR Y RECIBIR '
             'NOTIFICACIONES Y DOCUMENTOS DERIVADOS DE LA INTERPRETACIÓN Y '
             f'CUMPLIMIENTO DE ESTE CONVENIO LA EMPRESA {co}, EL UBICADO EN ', False),
            (dom_co, True),
            (f' Y EL C. {emp} EL UBICADO EN {dom_emp}', False),
        ])
        par([
            ('DÉCIMA PRIMERA.- ', True),
            (f'DECLARAN, LA EMPRESA {co} Y EL C. {emp}, QUE EL PRESENTE CONVENIO '
             'POR NO CONTENER CLÁUSULAS CONTRARIAS A LA MORAL O AL DERECHO Y POR '
             'ESTAR DENUNCIADO CONFORME A LO PREVISTO POR LOS ARTÍCULOS 33, Y '
             '53, FRACCIÓN I, DE LA LEY FEDERAL DEL TRABAJO VIGENTE, SE OBLIGAN '
             'A ESTAR Y PASAR POR EL EN TODO TIEMPO Y LUGAR COMO SI SE TRATARA '
             'DE COSA JUZGADA ASI TAMBIEN A RATIFICARLO EN EL MOMENTO QUE UNA '
             'PARTE REQUIERA A LA OTRA, ANTE EL CENTRO DE CONCILIACION LABORAL '
             'Y/O TRIBUNAL LABORAL Y/O CUALQUIER AUTORIDAD DONDE SE DEBA '
             'RATIFICAR YA SEA POR QUE ASI LO REQUIERA O POR QUE SEA NECESARIO, '
             'INCURRIENDO EN UNA RESPONSABILIDAD CIVIL Y/O PENAL EN CASO DE QUE '
             'ALGUNA DE LAS PARTES NO CUMPLA CON ESTA ULTIMA DISPOSICION, '
             'SITUACION QUE TAMBIEN RATIFICAN CON LOS ALCANCES JURIDICOS QUE DE '
             'ELLA SE DERIVEN', False),
        ])
        par([
            ('LEÍDO QUE FUE EN SU TOTALIDAD EL CONTENIDO DEL PRESENTE DOCUMENTO '
             f'POR LA EMPRESA {co}, EN SU CALIDAD DE PATRON Y RESPONSABLE DE LA '
             f'RELACION DE TRABAJO, EL C. {emp}, EN SU CALIDAD DE TRABAJADOR, Y '
             f'LAS C. {t1} Y {t2} EN SU CALIDAD DE TESTIGOS, LO FIRMAN Y '
             'RATIFICAN POR CONTENER EXACTAMENTE LOS TÉRMINOS EN QUE DESEAN '
             'OBLIGARSE, EN EL MUNICIPIO DE TLALNEPANTLA DE BAZ, ESTADO DE '
             f'MEXICO A {today}.', False),
        ])

        doc.add_paragraph()
        self._convenio_firmas_table(doc, co, emp)

        return _DocxBuilder.download(self.env, 'hr.employee', self.id,
                                     f'Convenio de Salida - {self.name}.docx',
                                     _DocxBuilder.to_bytes(doc))

    # --- Oficio de Remisión ---

    # Plantilla = oficio del sistema anterior (formato, textos y firmas idénticos);
    # solo se reemplazan razón social, nombre del empleado y fecha.
    REMISION_TEMPLATE = 'hr_estevez/data/templates/oficio_remision.docx'

    def action_download_remision_docx(self):
        self.ensure_one()
        values = {
            '{{EMPRESA}}': self._carta_patronal_company_name(),
            '{{EMPLEADO}}': self.name.upper(),
            '{{FECHA}}': _DocxBuilder.fmt_date(fields.Date.context_today(self)),
        }
        return _DocxBuilder.download(self.env, 'hr.employee', self.id,
                                     f'{self.name} - Oficio de Remisión.docx',
                                     _DocxBuilder.fill_template(self.REMISION_TEMPLATE, values))


class HrContractDocxReports(models.Model):
    _inherit = 'hr.contract'

    # --- Contrato Individual de Trabajo ---

    # Plantilla = contrato del sistema anterior (formato, cláusulas, anexos y firmas idénticos).
    # Solo se reemplazan los marcadores {{...}} con los datos del empleado y del contrato.
    CONTRACT_TEMPLATE = 'hr_estevez/data/templates/contrato_individual.docx'
    CONTRACT_GENDERS = {'male': 'MASCULINO', 'female': 'FEMENINO', 'indistinct': 'INDISTINTO'}
    CONTRACT_MARITAL = {
        'single': 'SOLTERO(A)', 'married': 'CASADO(A)', 'cohabitant': 'UNIÓN LIBRE',
        'widower': 'VIUDO(A)', 'divorced': 'DIVORCIADO(A)',
    }

    def _docx_from_template(self, template, values, filename):
        return _DocxBuilder.download(self.env, 'hr.contract', self.id, filename,
                                     _DocxBuilder.fill_template(template, values))

    @staticmethod
    def _contract_address(emp):
        """Domicilio como el contrato anterior: CALLE #NÚMERO, COLONIA C.P. 00000 CIUDAD, ESTADO."""
        text = emp.private_street or ''
        if emp.private_street2:
            text += f' #{emp.private_street2}'
        if emp.private_colonia:
            text += f', {emp.private_colonia}'
        if emp.private_zip:
            text += f' C.P. {emp.private_zip}'
        if emp.private_city:
            text += f' {emp.private_city}'
        if emp.private_state_id:
            text += f', {emp.private_state_id.name}'
        return text.strip(', ').upper()

    def action_download_contract_docx(self):
        self.ensure_one()
        emp = self.employee_id
        # El contrato anterior pone el país en español ("MÉXICO"), no el gentilicio
        spanish = next((code for code, _name in self.env['res.lang'].get_installed()
                        if code.startswith('es')), self.env.lang)
        country = emp.country_id.with_context(lang=spanish).name if emp.country_id else ''
        if emp.country_id.code == 'MX':
            country = 'México'  # con acento aunque no haya un idioma español instalado
        values = {
            '{{EMPRESA}}': emp._carta_patronal_company_name() if emp else (self.company_id.name or '').upper(),
            '{{EMPLEADO}}': emp.name.upper() if emp else '',
            '{{PUESTO}}': (self.job_id or emp.job_id).name.upper() if (self.job_id or emp.job_id) else '',
            '{{FECHA}}': _DocxBuilder.fmt_date(self.date_start) if self.date_start else '',
            '{{NACIONALIDAD}}': country.upper(),
            '{{EDAD}}': str(emp.age) if emp.age else '',
            '{{SEXO}}': self.CONTRACT_GENDERS.get(emp.gender, ''),
            '{{ESTADO_CIVIL}}': self.CONTRACT_MARITAL.get(emp.marital, ''),
            '{{CURP}}': (emp.curp or '').upper(),
            '{{RFC}}': (emp.rfc or '').upper(),
            '{{DOMICILIO}}': self._contract_address(emp),
        }
        return self._docx_from_template(self.CONTRACT_TEMPLATE, values,
                                        f'Contrato - {emp.name}.docx')

    # --- Addendum ---

    # Plantilla = addendum del sistema anterior (Arial 9 pt, listas numeradas, textos legales
    # y firmas). Solo se reemplazan los marcadores con los datos del empleado y la empresa,
    # así el formato queda idéntico al documento anterior.
    ADDENDUM_TEMPLATE = 'hr_estevez/data/templates/addendum_contrato.docx'

    def _addendum_values(self):
        employee = self.employee_id
        today = fields.Date.context_today(self)
        company_name = (employee._carta_patronal_company_name() if employee
                        else (self.company_id.name or 'N/A').upper())
        return {
            '{{EMPRESA}}': company_name,
            '{{EMPLEADO}}': employee.name.upper() if employee else 'N/A',
            '{{RFC_EMPRESA}}': ((employee.company_id or self.company_id).vat or 'N/A').replace(' ', '').upper(),
            '{{DIA}}': str(today.day),
            '{{MES}}': _DocxBuilder.MESES_ES[today.month],
            '{{ANIO}}': str(today.year),
        }

    def action_download_addendum_docx(self):
        self.ensure_one()
        return self._docx_from_template(self.ADDENDUM_TEMPLATE, self._addendum_values(),
                                        f'Addendum - {self.employee_id.name}.docx')
