# models/res_sucursal.py
from odoo import models, fields

class ResSucursal(models.Model):
    _name = 'res.sucursal'
    _description = 'Sucursales de Clientes'

    name = fields.Char(string='Identificación de la Sucursal', required=True)
    direccion = fields.Char(string='Dirección de la Sucursal')
    observaciones = fields.Text(string='Observaciones')
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
