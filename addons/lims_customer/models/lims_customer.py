# -*- coding: utf-8 -*-
from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Clientes'

    name = fields.Char(string="Nombre del Cliente", required=True)
    client_code = fields.Char(string="Código del Cliente")
    fiscal_address = fields.Char(string="Dirección Fiscal")

    # Relación con Sucursales (Una lista de sucursales para cada cliente)
    branch_ids = fields.One2many(
        'lims.branch',  # modelo hijo
        'customer_id',   # campo Many2one en el modelo hijo
        string="Sucursales"
    )
