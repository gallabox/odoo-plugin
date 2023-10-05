from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GcsWhatsappTemplateLineQuickReply(models.Model):
    _name = "gcs.whatsapp.template.line.quick.reply"
    _description = 'Whatsapp Template Line Quick Reply'

    button_name = fields.Char(string='Button Name')
    template_quick_reply = fields.Many2one('gcs.whatsapp.template')
