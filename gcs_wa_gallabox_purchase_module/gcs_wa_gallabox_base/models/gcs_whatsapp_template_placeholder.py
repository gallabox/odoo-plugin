from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GcsWhatsappTemplatePlaceholder(models.Model):
    _name = "gcs.whatsapp.template.placeholder"
    _description = 'Whatsapp Template Placeholder'

    field = fields.Many2one('ir.model.fields', string='Field')
    variable_name = fields.Char(string='Variable Name')

    template_placeholder_id = fields.Many2one('gcs.whatsapp.template')


    # @api.onchange('field')
    # def _onchange_field(self):
    #     """
    #     below code is written for passing the selected model's field ids to the field
    #     """
    #     ids = []
    #     model_ids = self.env['ir.model.fields'].search(
    #         [('model_id', '=', self.template_placeholder_id.model_id.id)])
    #     for recs in model_ids:
    #         ids.append(recs.id)
    #     return {'domain': {'field': [('id', 'in', ids)]}}
