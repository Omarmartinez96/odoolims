# models/res_sucursal.py
from odoo import models, fields

class ResSucursal(models.Model):
    _name = 'res.sucursal'
    _description = 'Sucursales de Clientes'

    name = fields.Char(string='Nombre de la Sucursal', required=True)
    direccion = fields.Char(string='Dirección')
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    departamentos_ids = fields.One2many(
        'res.departamento', 'sucursal_id', string='Departamentos'
    )
