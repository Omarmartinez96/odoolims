from odoo import models, fields

class LimsCustomer(models.Model):
    _name = "lims.customer"
    _description = "Cliente del LIMS"

    name = fields.Char(string="Nombre del Cliente", required=True)
    client_code = fields.Char(string="Código de Cliente", required=True)
    fiscal_address = fields.Text(string="Dirección Fiscal")

class LimsBranch(models.Model):
    _name = "lims.branch"
    _description = "Sucursales del Cliente"

    name = fields.Char(string="Nombre de la Sucursal", required=True)
    address = fields.Text(string="Dirección")
    customer_id = fields.Many2one("lims.customer", string="Cliente", required=True)

class LimsDepartment(models.Model):
    _name = "lims.department"
    _description = "Departamentos de la Sucursal"

    name = fields.Char(string="Nombre del Departamento", required=True)
    branch_id = fields.Many2one("lims.branch", string="Sucursal", required=True)

class LimsContact(models.Model):
    _name = "lims.contact"
    _description = "Contactos del Departamento"

    name = fields.Char(string="Nombre del Contacto", required=True)
    email = fields.Char(string="Correo Electrónico")
    phone = fields.Char(string="Teléfono")
    department_id = fields.Many2one("lims.department", string="Departamento", required=True)
