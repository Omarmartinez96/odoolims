from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Gestión de Clientes en LIMS'

    name = fields.Char(string="Nombre", required=True)
    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
