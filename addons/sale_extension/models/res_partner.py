# models/res_partner.py
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(
        string='Código de Cliente',
        help='Código único para identificar al cliente',
        index=True,  # Hacerlo buscable en la base de datos
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
        Sobreescribe el método create para asegurarse de que los contactos creados en
        'child_ids' se asocien automáticamente al cliente principal como contactos.
        """
        for vals in vals_list:
            if vals.get('parent_id'):
                vals['is_contact'] = True  # Marcar como contacto si tiene un cliente padre
        return super(ResPartner, self).create(vals_list)
