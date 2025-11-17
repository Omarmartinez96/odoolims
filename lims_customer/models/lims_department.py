# lims_department.py
from odoo import models, fields

class LimsDepartment(models.Model):
    _name = 'lims.department'
    _description = 'Departamentos'

    name = fields.Char(string="Nombre del Departamento", required=True)
    address = fields.Char(string="Dirección")

    # Campo Many2one apuntando a 'lims.branch'
    # (cada departamento pertenece a una sucursal)
    branch_id = fields.Many2one(
        'lims.branch',
        string="Sucursal",
        required=True
    )

    # Relación con Contactos
    contact_ids = fields.One2many(
        'lims.contact',      # modelo hijo
        'department_id',     # campo Many2one en el modelo hijo
        string="Contactos"
    )
