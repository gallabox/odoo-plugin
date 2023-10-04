from odoo import models, fields


class GcsInheritBaseConfig(models.Model):
    _inherit = 'gcs.whatsapp.config'

    confirm_in_purchase = fields.Boolean(string='Send Message On Confirm In Purchase')
