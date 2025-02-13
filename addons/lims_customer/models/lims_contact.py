from odoo import models, fields

class LimsContact(models.Model):
    _name = 'lims.contact'
    _description = 'Contacto'

    name = fields.Char(string="Nombre del Contacto", required=True)
    email = fields.Char(string="Correo Electrónico")
    phone = fields.Char(string="Teléfono")
    department_id = fields.Many2one('lims.department', string="Departamento", required=True)
