from odoo.exceptions import ValidationError
from odoo import models
import json
import requests
import os
import pytz
from datetime import datetime


class GcsGlobalFunction(models.Model):
    _name = 'gcs.global.function'
    _description = 'Global Function'

    # class GcsGlobalFunction:
    # This function makes a WhatsApp API call to send a message and logs the response.
    def whatsapp_api_call(self, recipient_id, template_id, replaced_field_values, body, record_id, variable_of_url):
        get_whatsapp_parameters = GcsGlobalFunction.get_and_check_whatsapp_parameters(self)
        partner_id = self.env['res.partner'].search([('id', '=', recipient_id)])
        config_model = self.env['gcs.whatsapp.config'].search([], limit=1)
        country_code = config_model.country_code
        template_model = self.env['gcs.whatsapp.template'].search([('id', '=', template_id)])

        model_name = template_model.model_id.model
        related_document = self.env[model_name].browse(record_id)

        base_url = related_document.get_base_url()
        get_url = related_document.get_portal_url(report_type='pdf', download=True)
        filtered_url = get_url.strip("(')")
        url = str(base_url) + str(filtered_url)
        phone_number = str(country_code) + str(partner_id.mobile)
        if variable_of_url:
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
        else:
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
        # Analyze the response to determine the message status.
        if response.text:
            response_json = json.loads(response.text)
            status = response_json.get('status')
            message_id = response_json.get('id')

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
            'partner_ids': partner_id.id,
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

    # This function retrieves and validates WhatsApp configuration parameters.
    def get_and_check_whatsapp_parameters(self):
        whatsapp_config = self.env['gcs.whatsapp.config'].search([])
        whatsapp_url = whatsapp_config.whatsapp_url
        whatsapp_api_secret = whatsapp_config.whatsapp_api_secret
        whatsapp_api_key = whatsapp_config.whatsapp_api_key
        whatsapp_channel_id = whatsapp_config.whatsapp_channel_id
        whatsapp_account_id = whatsapp_config.whatsapp_account_id

        # Check for missing parameters and raise a validation error if any are missing.
        if (not whatsapp_url or not whatsapp_api_secret or not whatsapp_api_key or not whatsapp_channel_id
                or not whatsapp_account_id):
            empty_fields = []
            if not whatsapp_url:
                empty_fields.append("WhatsApp URL")
            if not whatsapp_api_secret:
                empty_fields.append("WhatsApp API Secret")
            if not whatsapp_api_key:
                empty_fields.append("WhatsApp API Key")
            if not whatsapp_channel_id:
                empty_fields.append("WhatsApp Channel ID")

            raise ValidationError(
                "The following fields are empty in the WhatsApp configuration: {}".format(', '.join(empty_fields)))

        # Construct a dictionary with validated WhatsApp parameters.
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
                        # Construct the field access path for evaluation.
                        converted_field = 'record_ids.' + field_name
                        get_value = eval(converted_field)

                        timezone = pytz.timezone(user_timezone)
                        get_value = get_value.astimezone(timezone)
                        get_values = get_value.strftime('%Y-%m-%d %H:%M:%S')
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
            # print(replaced_field_values)
            # exit()
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
            return replaced_field_values, body, variable_of_url
