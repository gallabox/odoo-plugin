from odoo import fields, models, api
import requests
import base64
from .gcs_global_function import GcsGlobalFunction
from requests.exceptions import MissingSchema
import re

from odoo.exceptions import ValidationError


class GcsWhatsappConfig(models.Model):
    _name = 'gcs.whatsapp.config'
    _description = 'Whatsapp Configuration'
    _rec_name = 'id'

    whatsapp_url = fields.Char(string='URL', required=True)
    whatsapp_api_secret = fields.Char(string='API Secret', required=True)
    whatsapp_api_key = fields.Char(string='API Key', required=True)
    whatsapp_channel_id = fields.Char(string='Channel Id', required=True)
    whatsapp_phone_number = fields.Char(string='Phone Number')
    whatsapp_account_id = fields.Char(string='Account Id', required=True)
    country_code = fields.Integer(string='Country Code', default="91")
    status = fields.Selection([
        ('connected', 'Connected'), ('not_connected', 'Not Connected')], 'Status', readonly=True,
        default='not_connected',
        store=True)
    clear_log_interval = fields.Selection([
        ('never', 'Never'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], 'Clear Log Interval',
        default='never')

    @api.model
    def default_get(self, fields):
        res = super(GcsWhatsappConfig, self).default_get(fields)
        record_count = self.env['gcs.whatsapp.config'].search_count([])
        if record_count >= 1:
            raise ValidationError("You can only create one record for Configurations.")
        return res

    def set_template_language(self, template, vals):
        """
        This method stores the language id in the vals parameter
        """
        language = self.env['res.lang'].search([('iso_code', '=', template.get('language'))])
        if language:
            vals['language'] = language.id
        return vals

    def get_component_data(self, template, vals):
        """
        This method get the data of fields returns in the vals parameter
        """
        components = template.get('components', [])
        for component in components:
            format = component.get('format', '')
            format_mapping = {
                'VIDEO': 'video',
                'DOCUMENT': 'document',
                'IMAGE': 'image',
                'NONE': 'none',
                'TEXT': 'text',
            }
            message_type = format_mapping.get(format, '')
            if message_type:
                vals['message_type'] = message_type
            category_mapping = {
                'MARKETING': 'marketing',
                'UTILITY': 'utility'
            }
            category = category_mapping.get(template.get('category', ''), '')
            vals['name'] = template.get('name', '')
            vals['category'] = category

            if format == 'TEXT':
                text = component.get('text', '')
                vals['header'] = text

            if format in ['IMAGE', 'VIDEO', 'DOCUMENT']:
                file_path = component.get('filePath', '')
                if file_path:
                    response = requests.get(file_path)
                    if response.status_code == 200:
                        content = response.content
                        base64_data = base64.b64encode(content)
                        if format == 'IMAGE':
                            vals['image'] = base64_data
                        elif format == 'VIDEO':
                            vals['video'] = base64_data
                        elif format == 'DOCUMENT':
                            vals['document'] = base64_data
        return vals

    def process_template_components(self, template, vals):
        """
        This method get the data of fields form the template parameter and returns it in the vals parameter
        """
        components = template.get('components', [])
        for component in components:
            component_type = component.get('type')
            if component_type == 'BODY':
                body_text = component.get('text', '')
                vals['body'] = body_text
            elif component_type == 'FOOTER':
                footer_text = component.get('text', '')
                vals['footer'] = footer_text

            elif component_type == 'BUTTONS':
                buttons = component.get('buttons', [])
                for button in buttons:
                    button_type = button.get('type')
                    if button_type == 'PHONE_NUMBER':
                        phone_number_text = button.get('text', '')
                        phone_number = button.get('phone_number', '')
                        vals['phone_number'] = phone_number
                        vals['button_name_of_phone_number'] = phone_number_text
                        vals['phone_flag'] = True
                    elif button_type == 'URL':
                        if button.get('example'):
                            url_type = 'dynamic_url'
                            url = button.get('url', '')
                            example_url = button.get('example', '')
                            button_name_of_url = button.get('text', '')

                            vals['url_flag'] = True
                            vals['url'] = url
                            vals['url_type'] = url_type
                            vals['example_url'] = example_url
                            vals['button_name_of_url'] = button_name_of_url
                        else:
                            url_type = 'static_url'
                            url = button.get('url', '')
                            button_name_of_url = button.get('text', '')

                            vals['url_flag'] = True
                            vals['url'] = url
                            vals['url_type'] = url_type
                            vals['button_name_of_url'] = button_name_of_url
        return vals

    def create_variables_in_placeholders(self, template, created_whatsapp_template):
        """
        This function get the body variables form the template parameter and creates in the
        template placeholder model
        """
        placeholder_records = self.env['gcs.whatsapp.template.placeholder'].search([])
        components = template.get('components', [])
        # for component in components:
        #     component_type = component.get('type')
        #     if component_type == 'BODY':
        #         body_text = component.get('text', '')
        #         pattern = r"\{\{([^}]+)\}\}"
        #         variable_matches = re.findall(pattern, body_text)
        #         print(variable_matches)
        #         if variable_matches:
        #             for variable_name in variable_matches:
        #                 val = {
        #                     'template_placeholder_id': created_whatsapp_template.id,
        #                     'variable_name': variable_name
        #                 }
        #                 placeholder_records.create(val)

        for component in components:
            component_type = component.get('type')
            if component_type == 'BODY':
                body_text = component.get('text', '')
                pattern = r"\{\{([^}]+)\}\}"
                variable_match = re.findall(pattern, body_text)
                # Remove duplicates by converting to set and back to list
                variable_matches = sorted(set(variable_match))
                if variable_matches:
                    for variable_name in variable_matches:
                        val = {
                            'template_placeholder_id': created_whatsapp_template.id,
                            'variable_name': variable_name
                        }
                        placeholder_records.create(val)

    def create_quick_reply_text(self, template, created_whatsapp_template):
        """
        This button get the buttons data form template parameter and creates the buttons in the
        whatsapp template line quick reply model
        """
        quick_reply_text_records = self.env['gcs.whatsapp.template.line.quick.reply'].search([])
        components = template.get('components', [])
        for component in components:
            component_type = component.get('type')
            if component_type == 'BUTTONS':
                buttons = component.get('buttons', [])
                for button in buttons:
                    button_type = button.get('type')
                    if button_type == 'QUICK_REPLY':
                        quick_reply_text = button.get('text', '')
                        val = {
                            'template_quick_reply': created_whatsapp_template.id,
                            'button_name': quick_reply_text
                        }
                        quick_reply_text_records.create(val)

    def update_templates(self):
        """
        This method fetches WhatsApp templates from Whatsapp,
        it creates corresponding templates in the whatsapp template.
        """
        get_whatsapp_parameters = GcsGlobalFunction.get_and_check_whatsapp_parameters(self)
        try:
            payload = {}
            headers = {
                'apiKey': get_whatsapp_parameters['whatsapp_api_key'],
                'apiSecret': get_whatsapp_parameters['whatsapp_api_secret'],
                'Content-Type': 'application/json',
                'Cookie': 'connect.sid=s%3AvsbDcumLPApOKAZpLNkP1TNlRNpsZ0aV.80A%2B%2BdAmXnn7aXJbjX0dxk4v7YBLjX%2F%2FhsK1rGeWjAE'
            }
            response = requests.request("GET", get_whatsapp_parameters['whatsapp_url_for_get_template'],
                                        headers=headers, data=payload)
            if response.status_code == 200:
                templates = response.json()
                existing_whatsapp_template_name = self.env['gcs.whatsapp.template'].search([])
                template_names = []
                for name in existing_whatsapp_template_name:
                    template_names.append(name.name)

                for template in templates:
                    vals = {}
                    approved_templates = template.get('status')
                    approved_templates_names = template.get('name')
                    if approved_templates == 'approved':
                        if approved_templates == 'approved' and approved_templates_names not in template_names:
                            self.set_template_language(template, vals)
                            self.get_component_data(template, vals)
                            self.process_template_components(template, vals)

                            # Create a new WhatsApp template record with the extracted information.
                            whatsapp_template_create = self.env['gcs.whatsapp.template'].search([])
                            created_whatsapp_template = whatsapp_template_create.create(vals)
                            self.create_variables_in_placeholders(template, created_whatsapp_template)
                            self.create_quick_reply_text(template, created_whatsapp_template)

                self.write({
                    'status': 'connected',
                })
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': 'Templates Successfully Updated',
                        'type': 'rainbow_man',
                    }
                }
            else:
                raise ValidationError(
                    f"Provided configuration details are incorrect\n\n Response Status: {response.text}")

        except MissingSchema as e:
            error_message = f"Invalid URL: {e}"
            raise ValidationError(f"Invalid URL")
