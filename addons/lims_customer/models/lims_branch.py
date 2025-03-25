# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LimsBranch(models.Model):
    _name = 'lims.branch'
    _description = 'Sucursales'

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    address = fields.Char(string="Dirección")

    # ✅ CAMBIO CLAVE: Ahora apunta claramente a res.partner
    customer_id = fields.Many2one(
        'res.partner',
        string="Cliente",
        required=True,
        domain=[('is_lims_customer', '=', True)]
    )

    # Campos Computados para Mostrar Información del Cliente (sin cambios)
    customer_name = fields.Char(
        string="Nombre del Cliente", 
        compute='_compute_customer_info', 
        store=True, 
        readonly=True
    )
    client_code = fields.Char(
        string="Código del Cliente", 
        compute='_compute_customer_info', 
        store=True, 
        readonly=True
    )

    # Relación con Departamentos (sin cambios)
    department_ids = fields.One2many(
        'lims.department',
        'branch_id',
        string="Departamentos"
    )

    @api.depends('customer_id')
    def _compute_customer_info(self):
        for record in self:
            record.customer_name = record.customer_id.name if record.customer_id else ''
            record.client_code = record.customer_id.client_code if record.customer_id else ''
