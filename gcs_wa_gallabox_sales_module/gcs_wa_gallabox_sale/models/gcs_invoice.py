from odoo import models, fields, api
import base64
from odoo.exceptions import ValidationError
import os


class GcsInvoice(models.Model):
    _inherit = 'account.move'

    def gcs_invoice_popup(self):
        invoice_report_template_id = self.env.ref('account.account_invoices')._render_qweb_pdf(self.id)
        invoice_ref_no = self.name + '.pdf'
        invoice_ref = invoice_ref_no.replace('/', '-')
        attachments = []
        data_record = base64.b64encode(invoice_report_template_id[0])
        ir_values = {
            'name': invoice_ref,
            'type': 'binary',
            'datas': data_record,
            'store_fname': 'Invoice Reports.pdf',
            'mimetype': 'application/pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        attachments.append(data_id.id)

        model_id = self.env['ir.model'].search([('model', '=', 'account.move')])
        template_ids = self.env['gcs.whatsapp.template'].search([('model_id', '=', model_id.id)], limit=1)
        template_id = template_ids.id
        compose_form_id = self.env.ref('gcs_wa_gallabox_base.gcs_whatsapp_composer_view_form').id
        ctx = {
            'default_model': 'account.move',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_attachments': attachments,
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

    def action_post(self):
        res = super(GcsInvoice, self).action_post()
        config_model = self.env['gcs.whatsapp.config'].search([], limit=1)
        if config_model.confirm_in_sales_and_invoice:
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')])
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
                                                              replaced_field_values, body, record_id, variable_of_url)
        return res