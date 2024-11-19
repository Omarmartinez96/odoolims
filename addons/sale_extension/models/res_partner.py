# Archivo: models/res_partner.py
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    test_field = fields.Char(string='Test Field')  # Campo adicional de prueba
