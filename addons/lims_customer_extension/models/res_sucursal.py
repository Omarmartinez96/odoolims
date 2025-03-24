# res_sucursal.py
from odoo import models, fields

class ResSucursal(models.Model):
    _name = 'res.sucursal'
    _description = 'Sucursal del Cliente'

    name = fields.Char("Nombre de Sucursal", required=True)
    partner_id = fields.Many2one(
        'res.partner', 
        string="Cliente Principal", 
        domain="[('partner_type','=','customer')]",
        required=True
    )
    address = fields.Text("Dirección")
