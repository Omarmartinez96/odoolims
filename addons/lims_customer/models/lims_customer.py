# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LimsCustomer(models.Model):
    _inherit = 'res.partner'  # ✅ Herencia directa del modelo estándar de Odoo

    is_lims_customer = fields.Boolean(string='Cliente LIMS', default=True)
    rfc = fields.Char(string="RFC")
    client_code = fields.Char(string="Código del Cliente")
    fiscal_address = fields.Char(string="Dirección Fiscal")

    branch_ids = fields.One2many(
        'lims.branch',
        'customer_id',
        string="Sucursales"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_lims_customer'):
                if 'rfc' in vals and not vals.get('client_code'):
                    prefix = vals['rfc'][:3].upper() if vals['rfc'] else 'XXX'
                    existing_clients = self.search([('client_code', 'ilike', f'{prefix}-%')], order='client_code desc', limit=1)
                    last_number = int(existing_clients.client_code.split('-')[1]) if existing_clients else 0
                    vals['client_code'] = f"{prefix}-{str(last_number + 1).zfill(3)}"
        return super(LimsCustomer, self).create(vals_list)
