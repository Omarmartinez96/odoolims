# models/res_departamento.py
from odoo import models, fields, api

class ResDepartamento(models.Model):
    _name = 'res.departamento'
    _description = 'Departamentos en Sucursales'

    name = fields.Char(string='Nombre del Departamento', required=True)
    sucursal_id = fields.Many2one(
        'res.sucursal', string='Sucursal', required=True, ondelete='cascade',
        domain="[('cliente_id', '=', cliente_id)]",
        help='Sucursal a la que pertenece este departamento.'
    )
    cliente_id = fields.Many2one(
        'res.partner', string='Cliente', required=True, ondelete='cascade',
        help='Cliente relacionado a través de la sucursal.'
    )
    contactos_ids = fields.One2many(
        'res.partner', 'departamento_id', string='Contactos'
    )
    client_code = fields.Char(string='Código de Cliente', related='cliente_id.client_code', store=True)

    @api.onchange('sucursal_id')
    def _onchange_sucursal_id(self):
        """Actualizar cliente automáticamente al seleccionar la sucursal."""
        if self.sucursal_id:
            self.cliente_id = self.sucursal_id.cliente_id

    @api.model_create_multi
    def create(self, vals_list):
        """Asignar automáticamente cliente si se proporciona sucursal."""
        for vals in vals_list:
            if 'sucursal_id' in vals and vals['sucursal_id']:
                sucursal = self.env['res.sucursal'].browse(vals['sucursal_id'])
                vals['cliente_id'] = sucursal.cliente_id.id
        return super(ResDepartamento, self).create(vals_list)
