import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LimsContactInquiry(models.Model):
    _name = 'lims.contact.inquiry'
    _description = 'Solicitud de Contacto Comercial'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre del Contacto', required=True, tracking=True)
    company = fields.Char('Empresa / Organización')
    email = fields.Char('Correo Electrónico', required=True, tracking=True)
    phone = fields.Char('Teléfono / Celular')
    service_interest = fields.Selection([
        ('clinicos', 'Análisis Clínicos'),
        ('ambientales', 'Análisis Ambientales'),
        ('industriales', 'Análisis Industriales'),
        ('microbiologia', 'Microbiología'),
        ('fisicoquimicos', 'Análisis Fisicoquímicos'),
        ('alimentos', 'Análisis de Alimentos'),
        ('otro', 'Otro / No especificado'),
    ], string='Servicio de Interés', default='otro', required=True, tracking=True)
    subject = fields.Char('Asunto', required=True)
    message = fields.Text('Mensaje', required=True)
    state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('en_proceso', 'En Proceso'),
        ('atendido', 'Atendido'),
        ('cerrado', 'Cerrado'),
    ], string='Estado', default='nuevo', tracking=True)
    date = fields.Datetime(
        'Fecha de Solicitud',
        default=fields.Datetime.now,
        readonly=True,
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Asignado a',
        tracking=True,
        domain=[('share', '=', False)],
    )
    notes = fields.Text('Notas Internas')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Alta'),
        ('2', 'Urgente'),
    ], string='Prioridad', default='0')

    @api.constrains('email')
    def _check_email(self):
        email_pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValidationError(
                    'El correo electrónico "%s" no tiene un formato válido.' % record.email
                )

    def action_set_en_proceso(self):
        self.state = 'en_proceso'

    def action_set_atendido(self):
        self.state = 'atendido'

    def action_set_cerrado(self):
        self.state = 'cerrado'

    def _get_service_label(self):
        mapping = dict(self._fields['service_interest'].selection)
        return mapping.get(self.service_interest, self.service_interest)
