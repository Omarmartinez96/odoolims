from odoo import models, fields

class LimsCustomer(models.Model):
    _name = 'lims.customer'
    _description = 'Gestión de Clientes en LIMS'

    name = fields.Char(string="Nombre", required=True)
    rfc = fields.Char(string="RFC")  # <--- Asegúrate de que esta línea esté
    billing_partner_id = fields.Many2one('res.partner', string="Facturación")
    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
