# -*- coding: utf-8 -*-
from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Clientes'

    name = fields.Char(string="Nombre del Cliente", required=True)
    rfc = fields.Char(string="RFC")
    client_code = fields.Char(string="Código del Cliente")
    fiscal_address = fields.Char(string="Dirección Fiscal")

    # Relación con Sucursales (Una lista de sucursales para cada cliente)
    branch_ids = fields.One2many(
        'lims.branch',  # modelo hijo
        'customer_id',   # campo Many2one en el modelo hijo
        string="Sucursales"
    )

     @api.onchange('rfc')
    def _onchange_rfc(self):
        """Genera el Código del Cliente basado en los primeros 3 caracteres del RFC"""
        for record in self:
            if record.rfc and (not record.client_code or record.client_code == ''):
                record.client_code = record.rfc[:3].upper()