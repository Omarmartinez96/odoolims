from odoo import models, fields

class LimsContact(models.Model):
    _name = 'lims.contact'
    _description = 'Contactos de un Departamento'

    name = fields.Char(string="Nombre del Contacto", required=True)
    email = fields.Char(string="Correo Electrónico")
    phone = fields.Char(string="Teléfono")

    department_id = fields.Many2one('lims.department', string="Departamento", required=True, ondelete="cascade")
    branch_id = fields.Many2one('lims.branch', string="Sucursal", related="department_id.branch_id", store=True, readonly=True)
    customer_id = fields.Many2one('lims.customer', string="Cliente", related="branch_id.customer_id", store=True, readonly=True)
