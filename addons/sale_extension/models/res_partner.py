# models/res_partner.py
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(
        string='Código de Cliente',
        help='Código único para identificar al cliente',
        index=True,  # Hacerlo buscable en la base de datos
    )

    sucursales_ids = fields.One2many(
        'res.sucursal', 'cliente_id', string='Sucursales'
    )
