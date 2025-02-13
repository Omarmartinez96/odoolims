from odoo import models, fields

class LimsDepartment(models.Model):
    _name = "lims.department"
    _description = "Departamentos de Sucursal"

    name = fields.Char("Nombre del Departamento", required=True)
    branch_id = fields.Many2one("lims.branch", string="Sucursal", required=True)
    contact_ids = fields.One2many("lims.contact", "department_id", string="Contactos")
