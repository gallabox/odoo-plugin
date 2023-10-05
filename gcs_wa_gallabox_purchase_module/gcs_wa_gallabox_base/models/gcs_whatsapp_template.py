from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import requests


class GcsWhatsappTemplate(models.Model):
    "Templates for sending message on whatsapp"
    _name = "gcs.whatsapp.template"
    _description = 'Whatsapp Template'

    name = fields.Char('Name', translate=True)
    model_id = fields.Many2one(
        'ir.model', string='Applies to', domain=[('transient', '=', False)],
        help="The type of document this template can be used with", ondelete='cascade')
    body = fields.Text('Body', translate=True)
    language = fields.Many2one('res.lang', 'language')
    template_state = fields.Selection([
        ('confirm', 'Confirm'), ('set_to_draft', 'Set To draft')], 'State', default='set_to_draft')
    category = fields.Selection([
        ('marketing', 'Marketing'), ('utility', 'Utility'), ('authentication', 'Authentication')], 'Category')
    message_type = fields.Selection([
        ('none', 'None'), ('text', 'Text'), ('image', 'Image'), ('video', 'Video'), ('document', 'Document')], 'Type')
    header = fields.Text('Header')
    footer = fields.Text('Footer')
    image = fields.Binary(string='Image', store=True)
    document_fname_image = fields.Char(string='Image', store=True)
    video = fields.Binary(string='Video', store=True)
    document_fname_video = fields.Char(string='Video', store=True)
    document = fields.Binary(string='Document', store=True)
    document_fname_document = fields.Char(string='Document', store=True)
    phone_flag = fields.Boolean(string='')
    url_flag = fields.Boolean(string='Url Flag')
    phone_number = fields.Char(string='Phone')
    button_name_of_phone_number = fields.Char(string='Phone Button Name')
    url_type = fields.Selection([
        ('static_url', 'Static Url'), ('dynamic_url', 'Dynamic Url')], 'Url Type')
    button_name_of_url = fields.Char(string='Url Button Name')
    url = fields.Char(string='Url')
    example_url = fields.Char(string='Example Url')
    template_placeholder_id = fields.One2many('gcs.whatsapp.template.placeholder', 'template_placeholder_id')
    template_quick_reply = fields.One2many('gcs.whatsapp.template.line.quick.reply', 'template_quick_reply')
    active = fields.Boolean(default=True, string='Active')

    # Below method confirms the template by updating its state to 'confirm' on click button.
    def gcs_confirm_button(self):
        self.write({
            'template_state': 'confirm',
        })
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Template Confirmed',
                'type': 'rainbow_man',
            }
        }

    # Below method draft the template by updating its state to 'draft' on click button.
    def gcs_draft_button(self):
        self.write({
            'template_state': 'set_to_draft',
        })

    # Below constraint checks that each template placeholder has a field and a variable name assigned.
    @api.constrains('template_placeholder_id')
    def _check_template_placeholder_id(self):
        for record in self.template_placeholder_id:
            if not record.field:
                raise ValidationError('You must select the Field')
            if not record.variable_name:
                raise ValidationError('You must select the Variable Name')

    # This method overrides the default copy method to provide a default name for copied templates.
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {},
                       name=_("%s (copy)", self.name))
        return super(GcsWhatsappTemplate, self).copy(default=default)
