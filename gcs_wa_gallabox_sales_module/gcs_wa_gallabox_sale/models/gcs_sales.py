from odoo import models, fields, api
import base64
from odoo.exceptions import ValidationError


class GcsSale(models.Model):
    _inherit = 'sale.order'

    gcs_sales_flag = fields.Boolean(string='Flag', default=False)

    def gcs_popup(self):
        model_id = self.env['ir.model'].search([('model', '=', 'sale.order')])
        template_ids = self.env['gcs.whatsapp.template'].search([('model_id', '=', model_id.id)], limit=1)
        template_id = template_ids.id
        compose_form_id = self.env.ref('gcs_wa_gallabox_base.gcs_whatsapp_composer_view_form').id
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
        }
        return {
            'name': f"Send Message via Whatsapp",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'gcs.whatsapp.composer',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def _action_confirm(self):
        res = super(GcsSale, self)._action_confirm()
        config_model = self.env['gcs.whatsapp.config'].search([], limit=1)
        if config_model.confirm_in_sales_and_invoice:
            if self.gcs_sales_flag == False:
                model_id = self.env['ir.model'].search([('model', '=', 'sale.order')])
                template_model = self.env['gcs.whatsapp.template'].search([('model_id', '=', model_id.id)], limit=1)
                record_id = self.id
                template_id = template_model.id
                model_name = template_model.model_id.model
                recipient_id = self.partner_id.id
                get_replaced_field_values = self.env['gcs.global.function'].get_replaced_values(template_id, model_name,
                                                                                                record_id)
                if not get_replaced_field_values:
                    raise ValidationError('You must select the model name for field "Applies To" in Template')
                replaced_field_values = get_replaced_field_values[0]
                body = get_replaced_field_values[1]
                variable_of_url = get_replaced_field_values[2]
                self.env['gcs.global.function'].whatsapp_api_call(recipient_id, template_id,
                                                                  replaced_field_values, body, record_id,
                                                                  variable_of_url)

        return res
