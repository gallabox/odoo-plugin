from odoo import models, fields


class GcsInheritBaseConfig(models.Model):
    _inherit = 'gcs.whatsapp.config'

    confirm_in_sales_and_invoice = fields.Boolean(string='Send Message On Confirm In Sales and Invoice')
