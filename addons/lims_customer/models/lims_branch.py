from odoo import models, fields

class LimsBranch(models.Model):
    _name = "lims.branch"
    _description = "Sucursal del Cliente"

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    address = fields.Char(string="Dirección")
    customer_id = fields.Many2one('lims.customer', string="Cliente", required=True)

    department_ids = fields.One2many('lims.department', 'branch_id', string="Departamentos")
