from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Clientes en LIMS'
    _rec_name = 'name'

    name = fields.Char(string="Razón Social", required=True, unique=True)
    rfc = fields.Char(string="RFC", required=True)
    billing_partner_id = fields.Many2one(
        'res.partner',
        string="Facturar a",
        help="Razón social a la que se facturará (en el módulo nativo de Odoo)."
    )
    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
