import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LimsFeedback(models.Model):
    _name = 'lims.feedback'
    _description = 'Sugerencia, Queja o Felicitación'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre del Remitente', required=True, tracking=True)
    email = fields.Char('Correo Electrónico', required=True, tracking=True)
    feedback_type = fields.Selection([
        ('sugerencia', 'Sugerencia'),
        ('queja', 'Queja'),
        ('felicitacion', 'Felicitación'),
        ('consulta', 'Consulta General'),
    ], string='Tipo de Comentario', required=True, default='sugerencia', tracking=True)
    subject = fields.Char('Asunto')
    message = fields.Text('Descripción / Mensaje', required=True)
    sample_reference = fields.Char('Folio / Referencia de Muestra')
    service_date = fields.Date('Fecha del Servicio Recibido')
    state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('en_revision', 'En Revisión'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    ], string='Estado', default='nuevo', tracking=True)
    date = fields.Datetime(
        'Fecha de Envío',
        default=fields.Datetime.now,
        readonly=True,
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Responsable',
        tracking=True,
        domain=[('share', '=', False)],
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Alta'),
        ('2', 'Urgente'),
    ], string='Prioridad', default='0')
    resolution = fields.Text('Resolución / Respuesta Interna')

    @api.constrains('email')
    def _check_email(self):
        email_pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValidationError(
                    'El correo electrónico "%s" no tiene un formato válido.' % record.email
                )

    def action_set_en_revision(self):
        self.state = 'en_revision'

    def action_set_resuelto(self):
        self.state = 'resuelto'

    def action_set_cerrado(self):
        self.state = 'cerrado'
