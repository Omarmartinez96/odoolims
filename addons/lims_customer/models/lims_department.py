from odoo import models, fields

class LimsDepartment(models.Model):
    _name = 'lims.department'
    _description = 'Departamentos dentro de una Sucursal'

    name = fields.Char(string="Nombre del Departamento", required=True)
    
    branch_id = fields.Many2one('lims.branch', string="Sucursal", required=True, ondelete="cascade")
    customer_id = fields.Many2one('lims.customer', string="Cliente", related="branch_id.customer_id", store=True, readonly=True)
    
    contact_ids = fields.One2many('lims.contact', 'department_id', string="Contactos")
