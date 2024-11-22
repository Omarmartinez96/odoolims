# models/res_sucursal.py
from odoo import models, fields, api

class ResSucursal(models.Model):
    _name = 'res.sucursal'
    _description = 'Sucursales de Clientes'

    name = fields.Char(string='Identificación de la Sucursal', required=True)
    direccion = fields.Char(string='Dirección de la Sucursal')
    observaciones = fields.Text(string='Observaciones')
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    client_code = fields.Char(string='Código de Cliente', readonly=True)

    @api.onchange('cliente_id')
    def _onchange_cliente_id(self):
        """Actualizar client_code automáticamente al seleccionar cliente."""
        if self.cliente_id:
            self.client_code = self.cliente_id.client_code
