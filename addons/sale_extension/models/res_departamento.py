# models/res_departamento.py
from odoo import models, fields, api

class ResDepartamento(models.Model):
    _name = 'res.departamento'
    _description = 'Departamentos en Sucursales'

    name = fields.Char(string='Nombre del Departamento', required=True)
    sucursal_id = fields.Many2one('res.sucursal', string='Sucursal', required=True)
    client_code = fields.Char(string='Código de Cliente', readonly=True)

    @api.onchange('sucursal_id')
    def _onchange_sucursal_id(self):
        """Actualizar client_code automáticamente al seleccionar sucursal."""
        if self.sucursal_id:
            self.client_code = self.sucursal_id.client_code
