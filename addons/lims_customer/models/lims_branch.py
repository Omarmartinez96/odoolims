# -*- coding: utf-8 -*-
from odoo import models, fields

class LimsBranch(models.Model):
    _name = 'lims.branch'
    _description = 'Sucursales'

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    address = fields.Char(string="Dirección")

    # ✅ Campo Many2one (AQUÍ es donde se usa ondelete)
    customer_id = fields.Many2one(
        'lims.customer',
        string="Cliente",
        required=True,
        ondelete='cascade'  # ✅ Correcto uso aquí
    )

    # Relación con Departamentos (One2many sin ondelete)
    department_ids = fields.One2many(
        'lims.department',
        'branch_id',
        string="Departamentos"
    )
