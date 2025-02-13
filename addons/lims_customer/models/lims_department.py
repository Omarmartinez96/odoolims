from odoo import models, fields

class LimsDepartment(models.Model):
    _name = "lims.department"
    _description = "Departamentos de la Sucursal"

    name = fields.Char(string="Nombre del Departamento", required=True)

    branch_id = fields.Many2one('lims.branch', string="Sucursal", required=True)
    customer_id = fields.Many2one('lims.customer', string="Cliente", related="branch_id.customer_id", store=True)

    contact_ids = fields.One2many('lims.contact', 'department_id', string="Contactos")
