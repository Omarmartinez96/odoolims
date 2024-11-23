# models/res_sucursal.py
from odoo import models, fields

class ResSucursal(models.Model):
    _name = 'res.sucursal'
    _description = 'Sucursales de Clientes'

    name = fields.Char(string='Identificación de la Sucursal', required=True)
    direccion = fields.Char(string='Dirección de la Sucursal')
    observaciones = fields.Text(string='Observaciones')
    cliente_id = fields.Many2one(
        'res.partner', string='Cliente',
        required=True, ondelete='cascade',
        help='Cliente al que pertenece esta sucursal.'
    )
    contactos_ids = fields.One2many(
        'res.partner', 'sucursal_id', string='Contactos'
    )
    client_code = fields.Char(
        string='Código de Cliente',
        related='cliente_id.client_code',
        store=True,
        readonly=True,
        help='Código único del cliente asociado.'
    )
