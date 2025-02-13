from odoo import models, fields

class LimsCustomer(models.Model):
    _name = "lims.customer"
    _description = "Clientes LIMS"

    name = fields.Char("Nombre del Cliente", required=True)
    client_code = fields.Char("Código del Cliente")
    fiscal_address = fields.Char("Dirección Fiscal")
    branch_ids = fields.One2many("lims.branch", "customer_id", string="Sucursales")
