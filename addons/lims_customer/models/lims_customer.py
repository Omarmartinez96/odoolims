from odoo import models, fields

class LimsCustomer(models.Model):
    _name = "lims.customer"
    _description = "Cliente del LIMS"

    name = fields.Char(string="Nombre del Cliente", required=True)
    client_code = fields.Char(string="Código de Cliente")
    fiscal_address = fields.Text(string="Dirección Fiscal")

    branch_ids = fields.One2many('lims.branch', 'customer_id', string="Sucursales")
    department_ids = fields.One2many('lims.department', 'customer_id', string="Departamentos")
    contact_ids = fields.One2many('lims.contact', 'customer_id', string="Contactos")


class LimsBranch(models.Model):
    _name = 'lims.branch'
    _description = 'Sucursales del Cliente'

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    customer_id = fields.Many2one('lims.customer', string="Cliente", required=True, ondelete="cascade")
    address = fields.Text(string="Dirección")
    department_ids = fields.One2many('lims.department', 'branch_id', string="Departamentos")


class LimsDepartment(models.Model):
    _name = 'lims.department'
    _description = 'Departamentos de la Sucursal'

    name = fields.Char(string="Nombre del Departamento", required=True)
    branch_id = fields.Many2one('lims.branch', string="Sucursal", required=True, ondelete="cascade")
    customer_id = fields.Many2one('lims.customer', string="Cliente", required=True, ondelete="cascade")
    contact_ids = fields.One2many('lims.contact', 'department_id', string="Contactos")


class LimsContact(models.Model):
    _name = 'lims.contact'
    _description = 'Contactos del Departamento'

    name = fields.Char(string="Nombre del Contacto", required=True)
    email = fields.Char(string="Correo Electrónico")
    phone = fields.Char(string="Teléfono")
    department_id = fields.Many2one('lims.department', string="Departamento", required=True, ondelete="cascade")
    customer_id = fields.Many2one('lims.customer', string="Cliente", required=True, ondelete="cascade")
