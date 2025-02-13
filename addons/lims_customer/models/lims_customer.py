from odoo import models, fields

class LimsCustomer(models.Model):
    _name = "lims.customer"
    _description = "Cliente del LIMS"

    name = fields.Char(string="Nombre del Cliente", required=True)
    client_code = fields.Char(string="Código del Cliente")
    fiscal_address = fields.Text(string="Dirección Fiscal")

    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
