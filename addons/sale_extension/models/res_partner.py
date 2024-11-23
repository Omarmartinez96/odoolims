from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(string='Código de Cliente', help='Código único para identificar al cliente')
    sucursal_id = fields.Many2one(
        'res.sucursal', string='Sucursal',
        domain="[('cliente_id', '=', parent_id)]",
        help='Sucursal asociada al cliente principal.'
    )
    departamento_id = fields.Many2one(
        'res.departamento', string='Departamento',
        domain="[('sucursal_id', '=', sucursal_id)]",
        help='Departamento asociado a la sucursal seleccionada.'
    )
    is_contact = fields.Boolean(string='¿Es un contacto?', default=False)

    @api.onchange('parent_id', 'sucursal_id', 'departamento_id')
    def _onchange_related_fields(self):
        """Actualizar client_code dependiendo de la relación."""
        if self.parent_id:
            self.client_code = self.parent_id.client_code
        elif self.sucursal_id:
            self.client_code = self.sucursal_id.client_code
        elif self.departamento_id:
            self.client_code = self.departamento_id.client_code

    @api.model_create_multi
    def create(self, vals_list):
        """Heredar client_code al crear contactos."""
        for vals in vals_list:
            if 'parent_id' in vals and vals['parent_id']:
                parent = self.browse(vals['parent_id'])
                vals['client_code'] = parent.client_code
            elif 'sucursal_id' in vals and vals['sucursal_id']:
                sucursal = self.env['res.sucursal'].browse(vals['sucursal_id'])
                vals['client_code'] = sucursal.client_code
            elif 'departamento_id' in vals and vals['departamento_id']:
                departamento = self.env['res.departamento'].browse(vals['departamento_id'])
                vals['client_code'] = departamento.client_code
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        """Actualizar client_code al modificar contactos."""
        for record in self:
            if 'parent_id' in vals and vals['parent_id']:
                parent = self.browse(vals['parent_id'])
                vals['client_code'] = parent.client_code
            elif 'sucursal_id' in vals and vals['sucursal_id']:
                sucursal = self.env['res.sucursal'].browse(vals['sucursal_id'])
                vals['client_code'] = sucursal.client_code
            elif 'departamento_id' in vals and vals['departamento_id']:
                departamento = self.env['res.departamento'].browse(vals['departamento_id'])
                vals['client_code'] = departamento.client_code
        return super(ResPartner, self).write(vals)
