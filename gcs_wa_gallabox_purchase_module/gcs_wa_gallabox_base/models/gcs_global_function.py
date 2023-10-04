import pytz

from odoo.exceptions import ValidationError
from odoo import models, api, fields
import json
import requests


class GcsGlobalFunction(models.Model):
    _name = 'gcs.global.function'
    _description = 'Global Function'

    def whatsapp_api_call(self, recipient_id, template_id, replaced_field_values, body, record_id, variable_of_url):
        get_whatsapp_parameters = GcsGlobalFunction.get_and_check_whatsapp_parameters(self)
        partner_id = self.env['res.partner'].search([('id', '=', recipient_id)])

        config_model = self.env['gcs.whatsapp.config'].search([], limit=1)
        country_code = config_model.country_code
        template_model = self.env['gcs.whatsapp.template'].search([('id', '=', template_id)])
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        model_name = template_model.model_id.model
        related_document = self.env[model_name].browse(record_id)
        # phone_number = str(country_code) + str(partner_id.mobile)
        phone_number = '918151830493'
        if model_name == 'purchase.order':
            get_token = self.env['sale.order'].search([], limit=1)
            purchase_url = related_document.website_url
            url = base_url + purchase_url + '?access_token=%s' % (get_token.access_token)
            print(url, 'url1')

        elif model_name == 'sale.order' or model_name == 'account.invoice':
            base = related_document.portal_url
            get_url = base + '?access_token=%s' % (related_document.access_token)
            url = str(base_url) + str(get_url)
            print(url, 'url1')
        else:
            pass

        if variable_of_url:
            print('111')
            # Construct payload for the WhatsApp API.
            payload = {
                "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                "channelType": "whatsapp",
                "recipient": {
                    "name": partner_id.name,
                    "phone": phone_number
                },
                "whatsapp": {
                    "type": "template",
                    "template": {
                        "templateName": template_model.name,
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
            payload = {
                "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                "channelType": "whatsapp",
                "recipient": {
                    "name": partner_id.name,
                    "phone": phone_number
                },
                "whatsapp": {
                    "type": "template",
                    "template": {
                        "templateName": template_model.name,
                        "bodyValues": replaced_field_values,
                    }
                }
            }

        else:
            print('333')
            payload = {
                "channelId": get_whatsapp_parameters['whatsapp_channel_id'],
                "channelType": "whatsapp",
                "recipient": {
                    "name": partner_id.name,
                    "phone": phone_number
                },
                "whatsapp": {
                    "type": "template",
                    "template": {
                        "templateName": template_model.name,
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
        # Create a WhatsApp log entry to record the sent message.
        whatsapp_logs = self.env["gcs.whatsapp"]
        vals = {
            'partner_id': recipient_id,
            'state': state,
            'response': response,
            'body': body,
            'template_id': template_model.id,
            'message_id': message_id,
            'response_status': status,
            'record_id': record_id,
        }
        whatsapp_logs.create(vals)
        return response, state

    def get_and_check_whatsapp_parameters(self):
        """
           This function retrieves, validates and returns WhatsApp configuration parameters.
        """
        whatsapp_config = self.env['gcs.whatsapp.config'].search([])
        whatsapp_url = whatsapp_config.whatsapp_url
        whatsapp_api_secret = whatsapp_config.whatsapp_api_secret
        whatsapp_api_key = whatsapp_config.whatsapp_api_key
        whatsapp_channel_id = whatsapp_config.whatsapp_channel_id
        whatsapp_account_id = whatsapp_config.whatsapp_account_id

        if not whatsapp_url or not whatsapp_api_secret or not whatsapp_api_key or not whatsapp_channel_id or not whatsapp_account_id:
            empty_fields = []
            if not whatsapp_url:
                empty_fields.append("WhatsApp URL")
            if not whatsapp_api_secret:
                empty_fields.append("WhatsApp API Secret")
            if not whatsapp_api_key:
                empty_fields.append("WhatsApp API Key")
            if not whatsapp_channel_id:
                empty_fields.append("WhatsApp Channel ID")
            if not whatsapp_account_id:
                empty_fields.append("Account ID")

            raise ValidationError(
                "The following fields are empty in the WhatsApp configuration: {}".format(', '.join(empty_fields)))

        val = {
            'whatsapp_url': whatsapp_url + '/messages/whatsapp',
            'whatsapp_api_secret': whatsapp_api_secret,
            'whatsapp_api_key': whatsapp_api_key,
            'whatsapp_channel_id': whatsapp_channel_id,
            'whatsapp_url_for_get_template': whatsapp_url + '/accounts/' + whatsapp_account_id + '/whatsappTemplates',
        }
        return val

    def get_user_timezone(self):
        user_timezone = self.env.user.tz if hasattr(self.env.user, 'tz') else 'UTC'
        return user_timezone

    def get_replaced_values(self, template_id, model_name, record_id):
        user_timezone = self.get_user_timezone()
        get_template = self.env['gcs.whatsapp.template'].search([('id', '=', template_id)])
        if get_template:
            # print(model_name)
            # print(record_id)
            # print(template_id)
            record_ids = self.env[model_name].search([('id', '=', record_id)])
            replaced_field_values = {}  # storing the variable names and its field values in an dictionary
            # Replace template placeholders with actual field values from the record.

            for rec in get_template.template_placeholder_id:
                if rec.field:
                    field_type = rec.field.ttype
                    field_name = rec.field.name
                    # Check if the field type is not 'many2one' or 'many2many'.
                    if field_type not in ['many2one', 'many2many', 'datetime']:
                        # Construct the field access path for evaluation.
                        converted_field = 'record_ids.' + field_name
                        # Evaluate the constructed path to get the field value from the record.
                        get_values = eval(converted_field)
                        # Store the retrieved field value in the dictionary with the placeholder's variable name.
                        replaced_field_values[rec.variable_name] = get_values

                    elif field_type == 'datetime':
                        converted_field = 'record_ids.' + field_name
                        get_data = eval(converted_field)
                        get_value = fields.Datetime.from_string(get_data)
                        timezone = pytz.timezone(user_timezone)
                        get_time = get_value.astimezone(timezone)
                        get_values = get_time.strftime('%Y-%m-%d %H:%M:%S')
                        replaced_field_values[rec.variable_name] = get_values

                    elif field_type in ['many2one', 'many2many']:
                        # Check if the related model has a custom _rec_name field defined.
                        if rec.field.model_id._rec_name:
                            # Construct the field access path with _rec_name for evaluation.
                            converted_field = 'record_ids.' + field_name + '.' + rec.field.model_id._rec_name
                            # Evaluate the constructed path to get the formatted field value.
                            get_values = eval(converted_field)
                            if get_values:
                                # Store the formatted field value in the dictionary with the placeholder's variable name.
                                replaced_field_values[rec.variable_name] = get_values
                            else:
                                # If the formatted value is not available, proceed to the next iteration.
                                pass
                    else:
                        pass
            # Replace template placeholders in the template body with actual values.
            body = get_template.body
            for variable_name, value in replaced_field_values.items():
                placeholder = '{{' + variable_name + '}}'
                body = body.replace(placeholder, str(value))
            variable_of_url = ""
            for url_variable in get_template:
                if url_variable.url_type == 'dynamic_url' and url_variable.url:
                    get_variable = url_variable.url
                    # Iterate through the keys in replaced_field_values and replace placeholders in the URL.
                    for key in replaced_field_values:
                        placeholder = '{{' + key + '}}'
                        get_variable = get_variable.replace(placeholder, str(replaced_field_values[key]))
                    variable_of_url += get_variable
            # print('replaced_field_values',replaced_field_values)
            # print(body)
            # exit()
            return replaced_field_values, body, variable_of_url
