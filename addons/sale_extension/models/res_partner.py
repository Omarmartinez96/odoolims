# models/res_partner.py
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(
        string='Código de Cliente',
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
        Asignar automáticamente el `parent_id` y `is_contact` si es un contacto.
        """
        for vals in vals_list:
            if 'parent_id' in vals and vals['parent_id']:
                vals['is_contact'] = True  # Marcar como contacto si tiene cliente padre
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        """
        Forzar que los contactos no se conviertan en clientes independientes.
        """
        if 'parent_id' in vals and vals['parent_id']:
            vals['is_contact'] = True
        return super(ResPartner, self).write(vals)
