from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Clientes en LIMS'

    name = fields.Char(string="Nombre del Cliente", required=True)
    rfc = fields.Char(string="RFC")
    fiscal_address = fields.Char(string="Dirección Fiscal")
    client_code = fields.Char(string="Código del Cliente", required=True)
    
    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
