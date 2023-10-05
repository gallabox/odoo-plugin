# -*- coding: utf-8 -*-

{
    'name': 'Gcs Whatsapp Gallabox Base',
    'version': '1.0.0',
    'category': '',
    'depends': [
        'base'],
    "author": "Gallabox ,Geelani",
    "website": "https://www.geelani.com",
    'data': [
        'data/gcs_cron.xml',
        'views/gcs_whatsapp_template.xml',
        'views/gcs_whatspp_configuration.xml',
        "wizard/gcs_whatsapp_composer.xml",
        'views/gcs_whatsapp.xml',
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
