# models/res_partner.py
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sucursal_id = fields.Many2one(
        'res.sucursal', string='Sucursal', 
        help='Sucursal a la que pertenece este contacto'
    )
    departamento_id = fields.Many2one(
        'res.departamento', string='Departamento',
        help='Departamento dentro de la sucursal'
    )

    is_contact = fields.Boolean(
        string='¿Es un contacto?',
        default=False,
        help='Marca si este registro es un contacto'
    )
