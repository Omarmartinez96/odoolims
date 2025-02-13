from odoo import models, fields

class LimsContact(models.Model):
    _name = "lims.contact"
    _description = "Contactos del Departamento"

    name = fields.Char("Nombre del Contacto", required=True)
    email = fields.Char("Correo Electrónico")
    phone = fields.Char("Teléfono")
    department_id = fields.Many2one("lims.department", string="Departamento", required=True)
