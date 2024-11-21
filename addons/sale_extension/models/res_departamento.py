# models/res_departamento.py
from odoo import models, fields

class ResDepartamento(models.Model):
    _name = 'res.departamento'
    _description = 'Departamentos en Sucursales'

    name = fields.Char(string='Nombre del Departamento', required=True)
    sucursal_id = fields.Many2one('res.sucursal', string='Sucursal', required=True)
    contactos_ids = fields.One2many(
        'res.partner', 'departamento_id', string='Contactos'
    )
