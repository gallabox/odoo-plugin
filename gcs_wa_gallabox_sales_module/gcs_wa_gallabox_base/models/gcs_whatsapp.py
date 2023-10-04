from odoo import fields, models
import requests
import json
from .gcs_global_function import GcsGlobalFunction
from odoo.exceptions import ValidationError


class GcsWhatsapp(models.Model):
    _name = 'gcs.whatsapp'
    _description = 'Whatsapp Logs'
    _rec_name = 'id'
    _order = 'id DESC'

    body = fields.Text('Message')
    response = fields.Char('Response', readonly=True)
    # patient_id = fields.Many2one('medical.patient', string='Recipients')
    partner_id = fields.Many2one('res.partner', string='Recipients')
    attachments = fields.Many2many('ir.attachment', string='Attachment', attachment=True)
    state = fields.Selection([
        ('sent', 'Sent'), ('failed', 'Delivery Failed')], 'Status of the Message', readonly=True, copy=False,
        store=True)
    template_id = fields.Many2one('gcs.whatsapp.template', string='Template Id')
    message_id = fields.Char(string='Message Id')
    response_status = fields.Char(string='Response Status')
    record_id = fields.Integer(string='Record Id')

    # below button function is used for resending the messages in the logs
    def action_resend(self):
        """
        This button function resend the failed message;
        Check and validate the whatsapp config parameters;
        Trigger message and update the response and the message details
        """
        get_template_id = self.template_id
        if get_template_id:
            get_whatsapp_parameters = GcsGlobalFunction.get_and_check_whatsapp_parameters(self)
            model_id = self.env['ir.model'].search([('id', '=', get_template_id.model_id.id)])
            template_id = get_template_id.id
            model_name = model_id.model
            record_id = self.record_id
            config_model = self.env['gcs.whatsapp.config'].search([], limit=1)
            country_code = config_model.country_code
            # phone_number = str(country_code) + str(self.partner_id.mobile)
            phone_number = '918151830483'
            related_document = self.env[model_name].browse(record_id)
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            if model_name == 'purchase.order':
                get_token = self.env['sale.order'].search([], limit=1)
                purchase_url = related_document.website_url
                url = base_url + purchase_url + '?access_token=%s' % (get_token.access_token)
                print(url, 'url1')

            elif model_name == 'sale.order' or model_name == 'account.invoice':
                base = related_document.portal_url
                get_url = base + '?access_token=%s' % (related_document.access_token)
                url = str(base_url) + str(get_url)

            else:
                pass

            get_replaced_field_values = self.env['gcs.global.function'].get_replaced_values(template_id, model_name,
                                                                                            record_id)
            if not get_replaced_field_values:
                raise ValidationError('You must select the model name for field "Applies To" in Template')
            replaced_field_values = get_replaced_field_values[0]
            body = get_replaced_field_values[1]
            variable_of_url = get_replaced_field_values[2]

            if variable_of_url:
                # Construct payload for the WhatsApp API.
                payload = {
                    "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                    "channelType": "whatsapp",
                    "recipient": {
                        "name": self.partner_id.name,
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

            elif model_name != 'purchase.order' or model_name != 'sale.order' or model_name != 'account.invoice':
                print('2222')
                # Construct payload for the WhatsApp API request.
                payload = ({
                    "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                    "channelType": "whatsapp",
                    "recipient": {
                        "name": self.partner_id.name,
                        "phone": phone_number
                    },
                    "whatsapp": {
                        "type": "template",
                        "template": {
                            "templateName": get_template_id.name,
                            "bodyValues": replaced_field_values,
                        }
                    }
                })

            else:
                print('333')
                payload = {
                    "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                    "channelType": "whatsapp",
                    "recipient": {
                        "name": self.partner_id.name,
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
            print(response.text)
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
