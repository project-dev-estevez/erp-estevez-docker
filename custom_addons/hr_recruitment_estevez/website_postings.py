# -*- coding: utf-8 -*-
"""Contenido de las vacantes publicadas en el sitio web (sección Empleos).

Cada vacante se identifica por los posibles nombres del puesto (hr.job, sin importar mayúsculas
ni acentos) y su página se arma con
`render_posting`. El HTML resultante queda en `website_description`, así que después
se puede seguir editando desde el editor del sitio web.
"""
import logging
import unicodedata
from html import escape

_logger = logging.getLogger(__name__)

# Por ahora no se publica el sueldo (indicación de Dirección, 30/10/2026); los montos se conservan aquí
SHOW_SALARY = False

COMPANY_TAGLINE = "Estevez.Jor Servicios · Líderes en construcción de redes de fibra óptica y telecomunicaciones"

COMMON_BENEFITS = [
    ('fa-calendar-check-o', "Pagos puntuales", "Quincenales, los días 15 y último de cada mes."),
    ('fa-shield', "Prestaciones de ley desde el día 1", "IMSS, Infonavit, vacaciones, aguinaldo y prima vacacional."),
]

POSTINGS = [
    {
        'job': ["Coordinador de Almacén General", "Coordinador de Almacén"],
        'title': "Coordinador de Almacenes e Inventarios",
        'hook': "¿Tienes experiencia liderando equipos de almacén, manteniendo inventarios confiables y coordinando "
                "el abastecimiento de varios proyectos a la vez? Buscamos a una persona organizada y resolutiva que se "
                "anticipe a las necesidades de las obras y cuide la trazabilidad de los materiales.",
        'salary': "$23,000 a $28,000 MXN mensuales libres",
        'location': "Tlalnepantla Centro, Estado de México",
        'schedule': "Lunes a viernes de 8:00 a 18:00 h y sábados de 8:00 a 12:00 h",
        'mission': "Coordinar la operación del almacén general y los almacenes foráneos, supervisando a sus responsables y "
                   "asegurando el control, disponibilidad y trazabilidad de materiales, herramientas y equipos; planear el "
                   "abastecimiento junto con las áreas involucradas y dar seguimiento documental a cada movimiento y cierre de proyecto.",
        'benefits': COMMON_BENEFITS + [
            ('fa-home', "Proyectos foráneos", "Apoyo de alimentos, campamento gratuito y equipado, y traslados incluidos."),
            ('fa-line-chart', "Estabilidad y futuro", "Contratación directa, plan de carrera y aportaciones complementarias a tu AFORE."),
            ('fa-graduation-cap', "Capacitación", "Acceso a certificaciones constantes en el sector."),
            ('fa-laptop', "Herramientas de trabajo", "Equipo de cómputo, teléfono empresarial y herramientas especializadas."),
        ],
        'requirements': [
            "Licenciatura o Ingeniería en Logística, Ingeniería Industrial, Gestión Empresarial o carrera afín.",
            "Mínimo 3 años coordinando almacenes e inventarios y supervisando personal, de preferencia en construcción, telecomunicaciones, infraestructura u operaciones con proyectos foráneos.",
            "Dominio de inventarios físicos y digitales, conteos cíclicos, conciliaciones y auditorías.",
            "Capacidad para planear inventarios y reabasto junto con Proyectos, Operaciones, Compras, Abastecimiento y Control Vehicular.",
            "Excel intermedio o avanzado y manejo de ERP o plataformas de inventarios. Deseable NEODATA.",
            "Experiencia con KPI de almacén, máximos y mínimos, puntos de reorden y rotación de inventario.",
            "Liderazgo para organizar al equipo, delegar, dar seguimiento y atender urgencias en colaboración con otras áreas.",
            "Disponibilidad para viajar y licencia de conducir vigente (auto estándar).",
        ],
        'activities': [
            "Coordinar el almacén general y los foráneos, supervisando a sus responsables y atendiendo de 2 a 5 proyectos simultáneos.",
            "Planear con Proyectos, Operaciones, Compras, Abastecimiento y Control Vehicular los inventarios y el suministro de cada obra.",
            "Asegurar la correcta recepción, resguardo, surtido, entrega, devolución y transferencia de materiales, herramientas y equipos.",
            "Mantener información de inventarios confiable y actualizada, con trazabilidad y respaldo documental de cada movimiento.",
            "Programar conteos cíclicos e inventarios físicos; conciliar resultados e investigar diferencias hasta su aclaración.",
            "Diseñar y realizar auditorías internas en los almacenes, documentar hallazgos y verificar las acciones correctivas.",
            "Priorizar solicitudes entre obras cuando haya materiales limitados, aprovechando existencias antes de nuevas compras.",
            "Dar seguimiento a requisiciones, resguardos, recuperación de materiales y conciliaciones al cierre de cada proyecto.",
            "Elaborar y presentar reportes y KPI de inventarios, consumos, diferencias, surtimiento y auditorías.",
            "Asegurar el orden, la seguridad y el resguardo de materiales y activos, y el cumplimiento de los procedimientos internos.",
        ],
    },
    {
        'job': ["Coordinador de EHS"],
        'title': "Coordinador de Gestión EHS",
        'hook': "¿Tienes experiencia coordinando áreas de Seguridad, Salud Ocupacional y Medio Ambiente, liderando equipos "
                "multidisciplinarios y asegurando el cumplimiento documental? Buscamos un líder con visión estratégica para "
                "dirigir integralmente nuestra operación nacional de EHS.",
        'salary': "$25,000 a $30,000 MXN mensuales libres",
        'location': "Tlalnepantla Centro, Estado de México",
        'schedule': "Lunes a viernes de 8:00 a 18:00 h y sábado rotativo de 8:00 a 12:00 h",
        'mission': "Coordinar la operación integral del área de Seguridad, Salud Ocupacional y Medio Ambiente, garantizando el "
                   "cumplimiento legal, documental, ambiental y operativo de los proyectos mediante la correcta gestión de los equipos de EHS.",
        'benefits': COMMON_BENEFITS + [
            ('fa-cutlery', "Proyectos foráneos", "Apoyo de alimentos de $200 diarios libres (≈ $4,800 extra al mes)."),
            ('fa-home', "Hospedaje", "Campamento gratuito y equipado, con traslados incluidos."),
            ('fa-line-chart', "Estabilidad y futuro", "Contratación directa, plan de carrera y aportaciones complementarias a tu AFORE."),
            ('fa-graduation-cap', "Capacitación", "Acceso a certificaciones constantes en el sector."),
            ('fa-car', "Herramientas de trabajo", "Automóvil utilitario, equipo de cómputo, teléfono empresarial y herramientas especializadas."),
        ],
        'requirements': [
            "Ingeniería Ambiental, Industrial o afín a EHS (título y cédula indispensables).",
            "Mínimo 4 años coordinando áreas de EHS en construcción, infraestructura, telecomunicaciones o sectores similares.",
            "Experiencia liderando equipos multidisciplinarios de Seguridad, Salud Ocupacional y Medio Ambiente.",
            "Coordinación de auditorías internas, de clientes y requerimientos de la STPS.",
            "Integración y seguimiento de dossiers de seguridad, expedientes, evidencias de cumplimiento y control documental de proyectos.",
            "Conocimiento de la legislación aplicable: STPS, Protección Civil, SEMARNAT, PROFEPA, NOM e ISO 14001.",
            "Desarrollo de indicadores (KPI), reportes ejecutivos y tableros de control para Dirección.",
            "Disponibilidad para viajar ocasionalmente a los frentes de trabajo en todo el país.",
            "Saber conducir auto estándar y contar con licencia vigente (se aplica prueba de manejo).",
        ],
        'activities': [
            "Coordinar la operación nacional del área de Seguridad, Salud Ocupacional y Medio Ambiente.",
            "Dar seguimiento al desempeño del Supervisor de EHS, el Médico Laboral y el Auxiliar de EHS.",
            "Supervisar la integración de dossiers de seguridad, expedientes documentales y evidencias.",
            "Validar que la información de los Supervisores EHS cumpla con clientes, auditorías internas y autoridades.",
            "Coordinar la recopilación y el control documental para auditorías y verificaciones de la STPS.",
            "Dar seguimiento a los planes de acción derivados de auditorías e inspecciones.",
            "Supervisar campañas de salud ocupacional, programas preventivos y atención a emergencias.",
            "Coordinar investigaciones de incidentes y acciones preventivas y correctivas.",
            "Consolidar la información de todos los proyectos en reportes ejecutivos y detectar desviaciones para la mejora continua.",
            "Ser enlace ante autoridades (STPS, SEMARNAT, PROFEPA, etc.) y coordinar el Plan de Protección Civil.",
            "Gestionar el presupuesto anual de EPP, analizando requisiciones de cambio, devolución o descuento.",
        ],
    },
    {
        'job': ["Supervisor de EHS"],
        'title': "Supervisor de Seguridad e Higiene en Tramos Carreteros (Foráneo)",
        'hook': "¿Tienes experiencia supervisando seguridad en obras dentro de tramos carreteros y sabes hacer cumplir las "
                "medidas de seguridad con las cuadrillas? Buscamos a un profesional con conocimiento normativo, criterio para "
                "identificar riesgos y firmeza para intervenir en campo.",
        'salary': "$20,000 a $24,000 MXN mensuales libres",
        'location': "Base en Tlalnepantla Centro, Estado de México · Proyectos foráneos",
        'schedule': "Base: lunes a viernes de 8:00 a 18:00 h y sábados de 8:00 a 14:00 h",
        'mission': "Supervisar el cumplimiento de las medidas de Seguridad, Salud y Medio Ambiente en proyectos de redes de fibra "
                   "óptica en tramos carreteros, verificando la señalización y protección de las zonas de trabajo, el uso correcto "
                   "del EPP y las condiciones seguras de operación de cuadrillas propias y contratistas.",
        'benefits': COMMON_BENEFITS + [
            ('fa-cutlery', "Proyectos foráneos", "Apoyo de alimentos de $4,800 mensuales adicionales."),
            ('fa-home', "Hospedaje", "Campamento gratuito y equipado, con traslados incluidos."),
            ('fa-line-chart', "Estabilidad", "Contratación directa y aportaciones complementarias a tu AFORE."),
            ('fa-graduation-cap', "Capacitación", "Acceso a certificaciones constantes en el sector."),
            ('fa-car', "Herramientas de trabajo", "Unidad utilitaria asignada, equipo de cómputo, teléfono empresarial y EPP."),
        ],
        'requirements': [
            "Ingeniería Industrial, Ambiental o carrera afín.",
            "Indispensable: mínimo 3 años supervisando Seguridad e Higiene en obras de construcción, con participación comprobable en tramos carreteros.",
            "Conocimiento aplicado de la normativa de señalización temporal, dispositivos de protección y seguridad en obras carreteras.",
            "Experiencia verificando la instalación, ubicación, condiciones y mantenimiento de la señalización.",
            "Conocimiento de la normativa STPS para actividades de obra y trabajos de alto riesgo.",
            "Experiencia supervisando cuadrillas propias y contratistas, corrigiendo actos inseguros y exigiendo el uso del EPP.",
            "Capacidad para ejercer autoridad con firmeza y respeto, y manejar la resistencia del personal.",
            "Análisis de riesgos, inspecciones en campo, investigación de incidentes y elaboración de reportes.",
            "Conocimientos comprobables de primeros auxilios.",
            "Indispensable saber conducir auto estándar y contar con licencia vigente (se aplica prueba de manejo).",
            "Radicar en Ciudad de México o Estado de México, con disponibilidad para viajar y permanecer periodos prolongados en proyectos de otros estados.",
        ],
        'activities': [
            "Supervisar en campo las condiciones de seguridad de los trabajos en tramos carreteros.",
            "Verificar, antes y durante las actividades, la señalización temporal, delimitación y protección de las zonas de trabajo.",
            "Identificar riesgos por tránsito vehicular, maquinaria y actividades de las cuadrillas, y coordinar las medidas preventivas.",
            "Exigir y verificar el uso correcto del EPP en personal propio y contratistas.",
            "Intervenir ante actos y condiciones inseguras, suspender actividades cuando exista riesgo y escalar incumplimientos.",
            "Realizar recorridos, inspecciones y revisiones de materiales, herramientas y equipos.",
            "Impartir pláticas de seguridad e inducciones antes del inicio de labores.",
            "Elaborar análisis de riesgos, reportes, minutas y evidencias de cumplimiento.",
            "Investigar incidentes y accidentes y dar seguimiento a las acciones correctivas hasta su cierre.",
            "Coordinar simulacros, apoyar la atención de emergencias y atender los requerimientos de clientes y autoridades.",
        ],
    },
    {
        'job': ["Auxiliar de Gestión de Talento", "Auxiliar de Gestión de Personal"],
        'title': "Auxiliar de Gestión de Talento",
        'hook': "¿Eres una persona organizada, con gran atención al detalle y buscas crecer en Capital Humano? Buscamos un "
                "Auxiliar de Gestión de Talento con visión administrativa para fortalecer el control documental y la gestión "
                "de beneficios de nuestro personal.",
        'salary': "$12,000 MXN mensuales libres",
        'location': "Tlalnepantla Centro, Estado de México",
        'schedule': "Lunes a viernes de 8:00 a 18:00 h y sábado rotativo de 8:00 a 12:00 h",
        'mission': "Gestionar y controlar la documentación laboral, los planes de previsión social y los expedientes del personal, "
                   "asegurando la correcta integración de la información y el cumplimiento de los procesos administrativos con un servicio eficiente.",
        'benefits': COMMON_BENEFITS + [
            ('fa-line-chart', "Estabilidad", "Contratación directa y aportaciones complementarias a tu AFORE."),
            ('fa-graduation-cap', "Capacitación", "Acceso a certificaciones constantes en el sector."),
            ('fa-laptop', "Herramientas de trabajo", "Equipo de cómputo y teléfono empresarial."),
        ],
        'requirements': [
            "Licenciatura en Psicología, Administración, Pedagogía o afín.",
            "Mínimo 1 año en administración de personal con enfoque en Capital Humano, de preferencia en empresas de servicios a nivel nacional.",
            "Excel intermedio-avanzado y plataformas digitales de RH (ERP).",
            "Deseable: conocimiento de movimientos ante IMSS e Infonavit.",
            "Seguimiento de incidencias: faltas, incapacidades, permisos, tiempo por tiempo y descuentos.",
            "Comunicación efectiva, proactividad, orientación al servicio, empatía y trabajo en equipo.",
        ],
        'activities': [
            "Controlar la documentación del plan de pensiones y dar seguimiento a trámites de AFORE (devoluciones y aportaciones).",
            "Gestionar incidencias de nómina de varias razones sociales: faltas, retardos, incapacidades, permisos, descuentos, bonos y tiempo por tiempo.",
            "Realizar movimientos afiliatorios ante IMSS e Infonavit (altas, bajas y modificaciones salariales).",
            "Gestionar la renovación de contratos del personal administrativo y foráneo, anticipando vencimientos.",
            "Mantener actualizados los expedientes físicos y digitales, con trazabilidad y disponibilidad inmediata.",
            "Recabar y resguardar firmas en contratos, convenios y actas administrativas.",
            "Entregar y controlar los recibos de nómina (semanal y quincenal) con total confidencialidad.",
            "Asegurar que la documentación laboral esté respaldada en los repositorios digitales de la empresa.",
            "Atender las dudas de los colaboradores sobre pagos, descuentos y prestaciones.",
            "Apoyar la organización documental general del área conforme a los lineamientos internos.",
        ],
    },
    {
        'job': ["Auxiliar de Compras", "Analista de Compras"],
        'title': "Auxiliar de Compras",
        'hook': "¿Tienes experiencia en compras, facilidad para negociar y atención al detalle? Buscamos un Auxiliar de Compras "
                "que contribuya al abastecimiento oportuno de nuestros proyectos y áreas administrativas.",
        'salary': "$13,000 a $18,000 MXN mensuales libres",
        'location': "Tlalnepantla de Baz, Estado de México",
        'schedule': "Lunes a viernes de 8:00 a 18:00 h y sábados de 8:00 a 12:00 h",
        'mission': "Gestionar y dar seguimiento a la adquisición de bienes y servicios para la operación, desde la solicitud de "
                   "cotizaciones hasta la entrega y validación documental, cumpliendo presupuestos, políticas internas y tiempos de abastecimiento.",
        'benefits': COMMON_BENEFITS + [
            ('fa-line-chart', "Estabilidad y futuro", "Contratación directa, plan de carrera y aportaciones complementarias a tu AFORE."),
            ('fa-graduation-cap', "Capacitación", "Acceso a certificaciones constantes en el sector."),
            ('fa-laptop', "Herramientas de trabajo", "Equipo de cómputo y teléfono empresarial."),
        ],
        'requirements': [
            "Licenciatura en Administración de Empresas, Negocios, Gestión Empresarial o carrera afín.",
            "Mínimo 2 años de experiencia en compras, adquisiciones o abastecimiento de bienes y servicios.",
            "Excel intermedio para elaborar comparativos, analizar información y generar reportes.",
            "Experiencia con sistemas ERP para registrar y dar seguimiento a órdenes de compra.",
            "Negociación con proveedores, control presupuestal, revisión de facturas y seguimiento de contratos.",
            "Capacidad de análisis, organización, comunicación asertiva y actitud de servicio.",
            "Habilidad para atender solicitudes simultáneas y darles seguimiento hasta su cierre.",
        ],
        'activities': [
            "Recibir y revisar las requisiciones de compra: especificaciones, cantidades, presupuesto y fechas requeridas.",
            "Solicitar cotizaciones y elaborar comparativos de precio, calidad, disponibilidad, condiciones de pago y entrega.",
            "Buscar, evaluar y dar seguimiento a proveedores; negociar condiciones y mantener actualizadas sus listas de precios.",
            "Generar y dar seguimiento a las órdenes de compra en el ERP, con su documentación y autorizaciones.",
            "Coordinar con proveedores, almacén y áreas solicitantes la entrega oportuna de bienes y servicios.",
            "Consultar existencias y consumos con almacén para planear compras y evitar faltantes o compras innecesarias.",
            "Revisar que órdenes de compra, entregas y facturas coincidan, y canalizar la documentación para su pago.",
            "Atender incidencias por retrasos, diferencias, devoluciones, rechazos o incumplimientos de proveedores.",
            "Dar seguimiento administrativo a contratos, arrendamientos y servicios de mantenimiento.",
            "Elaborar reportes de compras, gasto por proveedor, ahorros y cumplimiento de entregas.",
        ],
        'extra_title': "Principales categorías de compra",
        'extra': [
            "Materiales, herramientas e insumos para almacén y operación",
            "Papelería, artículos de oficina y mobiliario",
            "Equipos de cómputo y licencias de software",
            "Servicios de limpieza, seguridad y mantenimiento",
            "Equipos de transporte y servicios asociados",
            "Arrendamiento de oficinas y campamentos",
            "Compras especiales solicitadas por Dirección",
        ],
    },
    {
        'job': ["Chofer"],
        'title': "Chofer Ejecutivo de Dirección General",
        'hook': "¿Tienes experiencia como Chofer Ejecutivo y te distingues por tu puntualidad, discreción y actitud de servicio? "
                "Buscamos a una persona responsable y confiable para apoyar directamente a Dirección General con traslados "
                "seguros, eficientes y puntuales.",
        'salary': "$15,000 MXN mensuales libres",
        'location': "Tlalnepantla Centro, Estado de México",
        'schedule': "Lunes a viernes de 8:00 a 18:00 h y sábados de 8:00 a 12:00 h · Variable según la agenda de Dirección General",
        'mission': "Garantizar traslados seguros, puntuales y eficientes con un servicio profesional, discreto y confiable, "
                   "adaptándose a la agenda de Dirección General y apoyando en las actividades operativas asignadas.",
        'benefits': COMMON_BENEFITS + [
            ('fa-line-chart', "Estabilidad", "Contratación directa y aportaciones complementarias a tu AFORE."),
            ('fa-car', "Herramientas de trabajo", "Vehículo utilitario y equipo telefónico."),
        ],
        'requirements': [
            "Bachillerato trunco o concluido.",
            "Mínimo 3 años como Chofer Ejecutivo, Chofer de Dirección, Chofer Particular o similar.",
            "Licencia de conducir vigente tipo A o E.",
            "Experiencia comprobable manejando vehículos automáticos y estándar.",
            "Disponibilidad de horario indispensable, según la agenda de Dirección General, y para traslados locales y eventualmente foráneos.",
            "Cartas de recomendación, referencias comprobables e historial laboral estable.",
            "Excelente presentación, puntualidad y actitud de servicio.",
            "Persona responsable, discreta, prudente y confiable.",
        ],
        'activities': [
            "Realizar los traslados personales y laborales de Dirección de forma segura, puntual y eficiente.",
            "Planificar rutas, tiempos de traslado y alternativas viales.",
            "Mantener disponibilidad y comunicación constante según la agenda de Dirección General.",
            "Apoyar en diligencias, compras y entrega o recolección de documentos y materiales.",
            "Mantener absoluta discreción sobre conversaciones, reuniones, ubicaciones e información de Dirección General.",
            "Verificar diariamente las condiciones mecánicas, limpieza, combustible y documentación del vehículo.",
            "Reportar oportunamente fallas, incidentes, servicios o mantenimientos requeridos.",
            "Cumplir el reglamento de tránsito, los protocolos de seguridad y las políticas internas.",
        ],
    },
]


def _items(items, icon):
    return "".join(
        f'<li><i class="fa {icon}" role="presentation"></i><span>{escape(item)}</span></li>' for item in items
    )


def render_posting(posting, apply_url):
    """HTML de la página de la vacante, con secciones editables desde el sitio web."""
    benefits = "".join(
        f'<div class="col-sm-6 col-lg-4"><div class="o_estevez_job_benefit">'
        f'<span class="o_estevez_job_benefit_icon"><i class="fa {icon}" role="presentation"></i></span>'
        f'<div><h6>{escape(title)}</h6><p>{escape(text)}</p></div></div></div>'
        for icon, title, text in posting['benefits']
    )
    salary = (
        f'<div><i class="fa fa-money" role="presentation"></i><span><small>Sueldo</small>{escape(posting["salary"])}</span></div>'
        if SHOW_SALARY else ""
    )
    extra = ""
    if posting.get('extra'):
        extra = (
            f'<div class="o_estevez_job_extra"><h3>{escape(posting["extra_title"])}</h3>'
            f'<div class="o_estevez_job_pills">'
            + "".join(f'<span>{escape(item)}</span>' for item in posting['extra'])
            + '</div></div>'
        )
    return f"""
<section class="o_estevez_job s_text_block o_colored_level">
  <div class="container">
    <div class="o_estevez_job_intro">
      <span class="o_estevez_job_tag">{escape(COMPANY_TAGLINE)}</span>
      <h2>{escape(posting['title'])}</h2>
      <p class="lead">{escape(posting['hook'])}</p>
      <div class="o_estevez_job_facts">
        {salary}
        <div><i class="fa fa-map-marker" role="presentation"></i><span><small>Lugar</small>{escape(posting['location'])}</span></div>
        <div><i class="fa fa-clock-o" role="presentation"></i><span><small>Horario</small>{escape(posting['schedule'])}</span></div>
      </div>
    </div>
    <div class="o_estevez_job_mission">
      <h3><i class="fa fa-bullseye" role="presentation"></i>Misión del puesto</h3>
      <p>{escape(posting['mission'])}</p>
    </div>
  </div>
</section>
<section class="o_estevez_job o_estevez_job_band s_text_block o_colored_level">
  <div class="container">
    <h3>Compensaciones y beneficios</h3>
    <div class="row g-3">{benefits}</div>
  </div>
</section>
<section class="o_estevez_job s_text_block o_colored_level">
  <div class="container">
    <div class="row g-4">
      <div class="col-lg-6">
        <h3>¿Qué buscamos?</h3>
        <ul class="o_estevez_job_list">{_items(posting['requirements'], 'fa-check-circle')}</ul>
      </div>
      <div class="col-lg-6">
        <h3>¿Qué harás?</h3>
        <ul class="o_estevez_job_list o_estevez_job_list_activities">{_items(posting['activities'], 'fa-angle-right')}</ul>
      </div>
    </div>
    {extra}
  </div>
</section>
<section class="o_estevez_job o_estevez_job_cta s_text_block o_colored_level">
  <div class="container">
    <h3>¿Eres la persona que buscamos?</h3>
    <p>Envíanos tu CV actualizado y forma parte del equipo de Estevez.Jor.</p>
    <a class="btn btn-lg o_estevez_job_cta_btn" href="{escape(apply_url)}">¡Postúlate ahora!</a>
  </div>
</section>
"""


def _normalize(text):
    text = unicodedata.normalize('NFD', text or '')
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn').casefold().strip()


def apply_postings(env, skip_published=False):
    """Activa y publica las vacantes de POSTINGS con su página. Devuelve las que no pudo publicar.

    skip_published: no toca las vacantes que ya tienen su página publicada (para no pisar ediciones).
    """
    Job = env['hr.job'].with_context(active_test=False)
    slug = env['ir.http']._slug
    langs = [lang for lang, _name in env['res.lang'].get_installed()]

    # Nombre normalizado (en cada idioma instalado) → puestos
    by_name = {}
    all_jobs = Job.search([])
    for lang in langs:
        for job in all_jobs.with_context(lang=lang):
            by_name.setdefault(_normalize(job.name), Job)
            by_name[_normalize(job.name)] |= job.with_env(Job.env)

    missing = []
    for posting in POSTINGS:
        jobs = Job
        for name in posting['job']:
            jobs = by_name.get(_normalize(name), Job)
            if jobs:
                break
        if len(jobs) != 1:
            label = posting['job'][0]
            missing.append(label if not jobs else f"{label} ({len(jobs)} coincidencias)")
            continue
        job = jobs
        if skip_published and job.is_published and 'o_estevez_job' in (job.website_description or ''):
            continue
        job.write({'active': True, 'no_of_recruitment': job.no_of_recruitment or 1})
        # Campos traducibles: se escriben en cada idioma para que no quede la plantilla anterior traducida
        content = {
            'description': f"<p>{escape(posting['hook'])}</p>",
            'website_description': render_posting(posting, f"/jobs/apply/{slug(job)}"),
        }
        for lang in langs:
            job.with_context(lang=lang).write(content)
        job.write({'is_published': True})
        _logger.info("Vacante publicada en el sitio web: %s", job.name)
    if missing:
        _logger.warning("Vacantes no encontradas (no se publicaron): %s", ", ".join(missing))
    return missing
