{
    'name': 'Google Meet Integration',
    'version': '1.0',
    'summary': 'Agrega enlaces de Google Meet a eventos',
    'depends': ['google_calendar', 'calendar'],
    'data': [
        'views/calendar_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': False,
}