from odoo import models, fields

class LimsDepartment(models.Model):
    _name = 'lims.department'
    _description = 'Departamentos en LIMS'

    name = fields.Char(string="Nombre del Departamento", required=True)
    branch_id = fields.Many2one('lims.branch', string="Sucursal", ondelete="cascade")
    
    contact_ids = fields.One2many('lims.contact', 'department_id', string="Contactos")
