# -*- coding: utf-8 -*-

{
    'name': 'Gcs Whatsapp Gallabox Base',
    'version': '1.0.0',
    'category': '',
    'depends': [
        'base'
    ],
    'author': '',
    'website': '',
    'data': [
        'data/gcs_cron.xml',
        'views/gcs_whatsapp_template.xml',
        'views/gcs_whatspp_configuration.xml',
        'views/gcs_whatsapp.xml',
        "wizard/gcs_whatsapp_composer.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
