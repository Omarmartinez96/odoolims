# -*- coding: utf-8 -*-
from odoo import models, fields

class LimsBranch(models.Model):
    _name = 'lims.branch'
    _description = 'Sucursales'

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    address = fields.Char(string="Dirección")

    # Campo Many2one apuntando a 'lims.customer'
    # (cada sucursal pertenece a un cliente)
    customer_id = fields.Many2one(
        'lims.customer',
        string="Cliente",
        required=True
    )

    # Relación con Departamentos (lista de departamentos para cada sucursal)
    department_ids = fields.One2many(
        'lims.department',  # modelo hijo
        'branch_id',        # campo Many2one en el modelo hijo
        string="Departamentos"
    )
