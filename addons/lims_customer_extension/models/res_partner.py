# res_partner.py
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection([
        ('customer', 'Cliente Principal'),
        ('contact', 'Contacto')
    ], string="Tipo de Registro", default='customer')

    client_code = fields.Char("Código Cliente", copy=False)
