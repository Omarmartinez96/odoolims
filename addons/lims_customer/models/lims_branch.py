from odoo import models, fields

class LimsBranch(models.Model):
    _name = "lims.branch"
    _description = "Sucursales de Clientes"

    name = fields.Char("Nombre de la Sucursal", required=True)
    address = fields.Char("Dirección")
    customer_id = fields.Many2one("lims.customer", string="Cliente", required=True)
    department_ids = fields.One2many("lims.department", "branch_id", string="Departamentos")
