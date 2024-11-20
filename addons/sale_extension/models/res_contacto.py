# models/res_contacto.py
from odoo import models, fields

class ResContacto(models.Model):
    _name = 'res.contacto'
    _description = 'Contactos de Departamentos'

    name = fields.Char(string='Nombre del Contacto', required=True)
    telefono = fields.Char(string='Teléfono')
    correo_electronico = fields.Char(string='Correo Electrónico')
    puesto = fields.Char(string='Puesto')
    departamento_id = fields.Many2one('res.departamento', string='Departamento', required=True)
