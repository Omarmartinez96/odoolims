# res_departamento.py
from odoo import models, fields

class ResDepartamento(models.Model):
    _name = 'res.departamento'
    _description = 'Departamento'

    name = fields.Char("Nombre Departamento", required=True)
    sucursal_id = fields.Many2one(
        'res.sucursal', 
        string="Sucursal", 
        required=True
    )
    description = fields.Text("Descripción del departamento")
