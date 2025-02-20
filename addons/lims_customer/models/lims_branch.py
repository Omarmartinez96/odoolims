# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LimsBranch(models.Model):
    _name = 'lims.branch'
    _description = 'Sucursales'

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    address = fields.Char(string="Dirección")

    # Campo Many2one apuntando a 'lims.customer'
    customer_id = fields.Many2one(
        'lims.customer',
        string="Cliente",
        required=True
    )

    # Campos Computados para Mostrar Información del Cliente
    customer_name = fields.Char(string="Nombre del Cliente", compute='_compute_customer_info', store=True, readonly=True)
    client_code = fields.Char(string="Código del Cliente", compute='_compute_customer_info', store=True, readonly=True)

    # Relación con Departamentos
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
