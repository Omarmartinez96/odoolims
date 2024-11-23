# models/res_departamento.py
from odoo import models, fields

class ResDepartamento(models.Model):
    _name = 'res.departamento'
    _description = 'Departamentos en Sucursales'

    name = fields.Char(string='Nombre del Departamento', required=True)
    sucursal_id = fields.Many2one(
        'res.sucursal', string='Sucursal', required=True, ondelete='cascade',
        help='Sucursal a la que pertenece este departamento.'
    )
    cliente_id = fields.Many2one(
        'res.partner', string='Cliente', related='sucursal_id.cliente_id', store=True,
        help='Cliente relacionado a través de la sucursal.'
    )
    contactos_ids = fields.One2many(
        'res.partner', 'departamento_id', string='Contactos'
    )
    client_code = fields.Char(string='Código de Cliente', related='cliente_id.client_code', store=True)
