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
        Sobreescribe el método create para:
        - Marcar como contacto (`is_contact = True`) si `parent_id` está definido.
        - Evitar que los contactos aparezcan como clientes independientes.
        """
        for vals in vals_list:
            if vals.get('parent_id'):
                vals['is_company'] = False  # No es una empresa
                vals['is_contact'] = True   # Es un contacto
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        """
        Sobreescribe el método write para asegurar que los contactos no se marquen
        como clientes independientemente.
        """
        if 'parent_id' in vals:
            for record in self:
                if vals.get('parent_id'):
                    vals['is_company'] = False
                    vals['is_contact'] = True
        return super(ResPartner, self).write(vals)