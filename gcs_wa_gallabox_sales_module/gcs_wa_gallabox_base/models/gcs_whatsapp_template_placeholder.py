from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GcsWhatsappTemplatePlaceholder(models.Model):
    _name = "gcs.whatsapp.template.placeholder"
    _description = 'Whatsapp Template Placeholder'

    field = fields.Many2one('ir.model.fields', string='Field')
    variable_name = fields.Char(string='Variable Name')
    template_placeholder_id = fields.Many2one('gcs.whatsapp.template')
