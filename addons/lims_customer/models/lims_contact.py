# lims_contact.py
from odoo import models, fields

class LimsContact(models.Model):
    _name = 'lims.contact'
    _description = 'Contactos'

    name = fields.Char(string="Nombre del Contacto", required=True)
    email = fields.Char(string="Correo Electrónico")
    phone = fields.Char(string="Teléfono")

    # Campo Many2one apuntando a 'lims.department'
    # (cada contacto pertenece a un departamento)
    department_id = fields.Many2one(
        'lims.department',
        string="Departamento",
        required=True
    )
