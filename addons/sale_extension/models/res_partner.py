from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(
        string='Código de Cliente',
        required=True,  # Hacer obligatorio
        help='Código único para identificar al cliente',
        index=True,
    )

    sucursal_id = fields.Many2one(
        'res.sucursal', string='Sucursal',
        help='Sucursal a la que pertenece este contacto'
    )
    departamento_id = fields.Many2one(
        'res.departamento', string='Departamento',
        help='Departamento dentro de la sucursal'
    )

    is_contact = fields.Boolean(
        string='¿Es un contacto?',
        default=False,
        help='Marca si este registro es un contacto'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Asignar automáticamente el `client_code` del cliente padre al crear un contacto.
        """
        for vals in vals_list:
            if vals.get('parent_id'):
                parent = self.browse(vals['parent_id'])
                vals['is_contact'] = True
                vals['client_code'] = parent.client_code  # Heredar código del cliente padre
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        """
        Asegurar que los contactos mantengan el mismo client_code que el cliente principal.
        """
        if 'parent_id' in vals and vals['parent_id']:
            parent = self.browse(vals['parent_id'])
            vals['is_contact'] = True
            vals['client_code'] = parent.client_code  # Actualizar client_code
        return super(ResPartner, self).write(vals)
