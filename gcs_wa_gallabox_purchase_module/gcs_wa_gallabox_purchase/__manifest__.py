# -*- coding: utf-8 -*-

{
    'name': 'Gcs Whatsapp Gallabox Purchase',
    'version': '1.0.0',
    'category': '',
    'depends': [
        'base', 'purchase', 'gcs_wa_gallabox_base'],
    "author": "Gallabox ,Geelani",
    "website": "https://www.geelani.com",
    'data': [
        "views/gcs_purchase.xml",
        "views/gcs_inherit_base_config.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
