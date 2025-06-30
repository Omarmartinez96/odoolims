from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    lims_branch_id = fields.Many2one(
        'lims.branch', 
        string="Sucursal LIMS",
        domain="[('customer_id', '=', partner_id)]"
    )

    lims_department_id = fields.Many2one(
        'lims.department',
        string="Departamento",
        domain="[('branch_id', '=', lims_branch_id)]"
    )

    lims_contact_id = fields.Many2one(
        'lims.contact',
        string="Contacto",
        domain="[('department_id', '=', lims_department_id)]"
    )
