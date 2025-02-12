from odoo import models, fields

class LimsBranch(models.Model):
    _name = 'lims.branch'  # ✅ ESTE NOMBRE SE USA EN ir.model.access.csv
    _description = 'Sucursales en LIMS'

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    customer_id = fields.Many2one('lims.customer', string="Cliente", ondelete="cascade")
    address = fields.Char(string="Dirección")

    department_ids = fields.One2many('lims.department', 'branch_id', string="Departamentos")
