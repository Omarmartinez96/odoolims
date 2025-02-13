from odoo import models, fields

class LimsCustomer(models.Model):
    _name = "lims.customer"
    _description = "Cliente del LIMS"

    name = fields.Char(string="Nombre del Cliente", required=True)
    rfc = fields.Char(string="RFC")
    billing_partner_id = fields.Many2one('res.partner', string="Empresa Facturadora")

    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
    contact_ids = fields.One2many('lims.contact', 'customer_id', string="Contactos")
