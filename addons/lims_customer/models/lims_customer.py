# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Clientes'

    name = fields.Char(string="Nombre del Cliente", required=True)
    rfc = fields.Char(string="RFC")
    client_code = fields.Char(string="Código del Cliente")
    fiscal_address = fields.Char(string="Dirección Fiscal")

    # Relación con Sucursales
    branch_ids = fields.One2many(
        'lims.branch',
        'customer_id',
        string="Sucursales"
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Genera el Código del Cliente basado en el RFC y número consecutivo"""
        for vals in vals_list:
            if 'rfc' in vals and not vals.get('client_code'):
                prefix = vals['rfc'][:3].upper() if vals['rfc'] else 'XXX'
                existing_clients = self.search([('client_code', 'ilike', f'{prefix}-%')], order='client_code desc', limit=1)
                if existing_clients:
                    last_number = int(existing_clients.client_code.split('-')[1])
                else:
                    last_number = 0
                new_code = f"{prefix}-{str(last_number + 1).zfill(3)}"
                vals['client_code'] = new_code
        return super(LimsCustomer, self).create(vals_list)
