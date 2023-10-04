from odoo import api, fields, models
from ast import literal_eval
from odoo.exceptions import ValidationError


class GcsWhatsappComposer(models.TransientModel):
    _name = 'gcs.whatsapp.composer'
    _description = 'Send Whatsapp Wizard'

    @api.model
    def default_get(self, fields):
        result = super(GcsWhatsappComposer, self).default_get(fields)
        result['res_model'] = result.get('res_model') or self.env.context.get('active_model')
        if not result.get('res_ids'):
            if not result.get('res_id') and self.env.context.get('active_ids') and len(
                    self.env.context.get('active_ids')) > 1:
                result['res_ids'] = repr(self.env.context.get('active_ids'))
        if not result.get('res_id'):
            if not result.get('res_ids') and self.env.context.get('active_id'):
                result['res_id'] = self.env.context.get('active_id')
        return result

    res_model = fields.Char('Document Model Name')
    res_model_description = fields.Char('Document Model Description', compute='_compute_res_model_description')
    res_id = fields.Integer('Document ID')
    res_ids = fields.Char('Document IDs')
    template_id = fields.Many2one('gcs.whatsapp.template', string='Use Template', store=True)
    body = fields.Text(string='Message')
    gcs_partner_ids = fields.Many2many('res.partner', string='Recipient Name', readonly=False, store=True)
    # compute = '_onchange_res_model',precompute=True,
    attachments = fields.Many2many('ir.attachment', string='Attach a file', attachment=True)

    @api.onchange('res_model', 'res_id', 'template_id')
    def _onchange_res_model(self):
        for record in self:
            records_data = record._get_records()
            record.gcs_partner_ids = records_data['partner_id']
            template_id = record.template_id.id
            model_name = record.res_model
            record_id = records_data.id
            get_replaced_field_values = self.env['gcs.global.function'].get_replaced_values(template_id, model_name,
                                                                                            record_id)
            if get_replaced_field_values:
                record.body = get_replaced_field_values[1]

    def _get_records(self):
        if not self.res_model:
            return None
        if self.res_ids:
            records = self.env[self.res_model].browse(literal_eval(self.res_ids))
        elif self.res_id:
            records = self.env[self.res_model].browse(self.res_id)
        else:
            records = self.env[self.res_model]

        records = records.with_context(mail_notify_author=True)
        return records

    def action_send_whatsapp(self):
        recipient_ids = self.gcs_partner_ids
        for rec in recipient_ids:
            template_id = self.template_id.id
            get_records = self._get_records()
            model_name = self.res_model
            record_id = get_records.id
            get_replaced_field_values = self.env['gcs.global.function'].get_replaced_values(template_id, model_name,
                                                                                            record_id)
            if not get_replaced_field_values:
                raise ValidationError('You must select the model name for field "Applies To" in Template')
            replaced_field_values = get_replaced_field_values[0]
            body = get_replaced_field_values[1]
            variable_of_url = get_replaced_field_values[2]
            recipient_id = rec.id
            self.env['gcs.global.function'].whatsapp_api_call(recipient_id, template_id,
                                                              replaced_field_values, body,
                                                              record_id, variable_of_url)
