from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Cliente LIMS'

    name = fields.Char(string="Nombre del Cliente", required=True)
    client_code = fields.Char(string="Código de Cliente")
    fiscal_address = fields.Char(string="Dirección Fiscal")

    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
