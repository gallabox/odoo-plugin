from odoo import fields, models
import requests
import json
from .gcs_global_function import GcsGlobalFunction
from odoo.exceptions import ValidationError
import os


class GcsWhatsapp(models.Model):
    _name = 'gcs.whatsapp'
    _description = 'Whatsapp Logs'
    _rec_name = 'id'
    _order = 'id DESC'

    body = fields.Text('Message')
    response = fields.Char('Response', readonly=True)
    partner_ids = fields.Many2one('res.partner', string='Recipients')
    attachments = fields.Many2one('ir.attachment', string='Attachment', attachment=True)
    state = fields.Selection([
        ('sent', 'Sent'), ('failed', 'Delivery Failed')], 'Status of the Message', readonly=True, copy=False,
        store=True)
    template_id = fields.Many2one('gcs.whatsapp.template', string='Template Id')
    message_id = fields.Char(string='Message Id')
    response_status = fields.Char(string='Response Status')
    record_id = fields.Integer(string='Record Id')

    # below button function is used for resending the messages in the logs
    def action_resend(self):
        get_template_id = self.template_id
        if get_template_id:
            # Get WhatsApp parameters and ensure they are properly configured.
            get_whatsapp_parameters = GcsGlobalFunction.get_and_check_whatsapp_parameters(self)

            # Get the model associated with the template and its corresponding data.
            model_id = self.env['ir.model'].search([('id', '=', get_template_id.model_id.id)])
            template_id = get_template_id.id
            model_name = model_id.model
            record_id = self.record_id

            config_model = self.env['gcs.whatsapp.config'].search([], limit=1)
            country_code = config_model.country_code
            phone_number = str(country_code) + str(self.partner_ids.mobile)
            related_document = self.env[model_name].browse(record_id)

            base_url = related_document.get_base_url()
            get_url = related_document.get_portal_url(report_type='pdf', download=True)
            filtered_url = get_url.strip("(')")
            url = str(base_url) + str(filtered_url)
            get_replaced_field_values = self.env['gcs.global.function'].get_replaced_values(template_id, model_name,
                                                                                            record_id)

            if not get_replaced_field_values:
                raise ValidationError('You must select the model name for field "Applies To" in Template')
            replaced_field_values = get_replaced_field_values[0]
            body = get_replaced_field_values[1]
            variable_of_url = get_replaced_field_values[2]

            # Construct payload for the WhatsApp API request.
            if variable_of_url:
                # Construct payload for the WhatsApp API.
                payload = {
                    "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                    "channelType": "whatsapp",
                    "recipient": {
                        "name": self.partner_ids.name,
                        "phone": phone_number
                    },
                    "whatsapp": {
                        "type": "template",
                        "template": {
                            "templateName": get_template_id.name,
                            "headerValues": {
                                "mediaUrl": url,
                                "mediaName": "Report"
                            },

                            "bodyValues": replaced_field_values,
                            "buttonValues": [
                                {
                                    "index": 1,
                                    "sub_type": "url",
                                    "parameters": {
                                        "type": "text",
                                        "text": variable_of_url
                                    }
                                }
                            ]
                        }
                    }
                }
            else:
                payload = {
                    "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                    "channelType": "whatsapp",
                    "recipient": {
                        "name": self.partner_ids.name,
                        "phone": phone_number
                    },
                    "whatsapp": {
                        "type": "template",
                        "template": {
                            "templateName": get_template_id.name,
                            "headerValues": {
                                "mediaUrl": url,
                                "mediaName": "Report"
                            },
                            "bodyValues": replaced_field_values,
                        }
                    }
                }

            # Prepare headers for the API request.
            headers = {
                'apiKey': get_whatsapp_parameters['whatsapp_api_key'],
                'apiSecret': get_whatsapp_parameters['whatsapp_api_secret'],
                'Content-Type': 'application/json',
                'Cookie': 'connect.sid=s%3AZvfZsbZ2dtv7nkRpkHdEgGEpVgOafGbF.uQg6BBqK8fvGm4hrY82ybDl8Nd451E1DJLYkMEdH7AE'
            }

            # Send the API request and process the response.
            response = requests.request("POST", get_whatsapp_parameters['whatsapp_url'], headers=headers, json=payload)
            # Analyze the response to determine the message status.

            if response.text:
                response_json = json.loads(response.text)
                status = response_json.get('status')  # Get the 'status' value from the JSON
                message_id = response_json.get('id')  # Get the 'message_id' value from the JSON
                if status == 'ACCEPTED':
                    state = 'sent'
                    response = response_json
                else:
                    state = 'failed'
                    response = response_json
            else:
                state = 'failed'
                response = "Message not sent"
                message_id = " "
                status = " "
                # Updating the WhatsApp log of the current record
            self.write({
                'state': state,
                'response': response,
                'message_id': message_id,
                'response_status': status,
                'body': body,
            })
