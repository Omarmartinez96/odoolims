from datetime import datetime
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=False, index=True, default='/')

    client_code = fields.Char(
        string="Código del Cliente",
        related='partner_id.client_code',
        readonly=True,
        store=True
    )

    lims_branch_id = fields.Many2one(
        'lims.branch', 
        string="Sucursal",
        domain="[('customer_id', '=', partner_id)]"
    )

    lims_department_id = fields.Many2one(
        'lims.department',
        string="Departamento",
        domain="[('branch_id', '=', lims_branch_id)]"
    )

    lims_contact_ids = fields.Many2many(
        'lims.contact',
        'sale_order_lims_contact_rel',  # tabla relacional
        'order_id',                     # campo en sale.order
        'contact_id',                   # campo en lims.contact
        string="Contactos",
        domain="[('department_id', '=', lims_department_id)]"
    )

    @api.model_create_multi
    def create(self, vals_list):
        year = str(datetime.today().year)

        for vals in vals_list:
            if vals.get('name', '/') == '/':
                # Buscar todas las cotizaciones con ese año en el nombre
                existing = self.search([
                    ('name', 'like', f'%/{year}'),
                    ('name', '!=', '/')
                ])

                # Obtener el mayor consecutivo existente
                def extract_number(name):
                    try:
                        return int(name.split('/')[0])
                    except Exception:
                        return 0

                max_num = max([extract_number(rec.name) for rec in existing], default=0)
                next_num = str(max_num + 1).zfill(3)
                vals['name'] = f'{next_num}/{year}'

        return super(SaleOrder, self).create(vals_list)
    
    @api.onchange('partner_id')
    def _onchange_partner_id_currency(self):
        if self.partner_id and self.partner_id.country_id:
            if self.partner_id.country_id.code == 'US':
                usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd:
                    self.currency_id = usd