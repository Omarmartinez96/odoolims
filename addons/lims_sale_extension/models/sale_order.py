from datetime import datetime
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

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

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            year = datetime.today().year
            seq = self.env['ir.sequence'].next_by_code('sale.order.lims') or '000'
            vals['name'] = f'{seq}/{year}'
        return super(SaleOrder, self).create(vals)