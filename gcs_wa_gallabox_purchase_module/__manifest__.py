# -*- coding: utf-8 -*-

{
    'name': 'Gcs Whatsapp Gallabox Odoo Module For Purchase',
    "author": "Geelani Consultancy & Solutions, Gallabox",
    'version': '1.0.0',
    "website": "https://gallabox.com/",
    'description': """
        Enhance your Odoo experience with the Gallabox WhatsApp Purchase Order Integration module. This powerful extension seamlessly integrates Gallabox with Odoo, allowing you to effortlessly send purchase order details to customers via WhatsApp. Whether you want to automate the process or send them manually, this module simplifies communication and enhances customer engagement.""",
    'category': '',
    'depends': [
        'base'
    ],
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
