from datetime import datetime
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    name = fields.Char(string='Número', required=True, copy=False, readonly=False, index=True, default='/')

    @api.model
    def _get_sequence_prefix_suffix(self):
        """Deshabilitar secuencia automática para facturas"""
        if self.move_type == 'out_invoice':
            return '', ''  # Sin prefijo ni sufijo automático
        return super()._get_sequence_prefix_suffix()

    def _set_next_sequence(self):
        """Evitar que Odoo asigne secuencia automática"""
        if self.move_type == 'out_invoice':
            return  # No hacer nada, usar nuestro formato
        return super()._set_next_sequence()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (vals.get('move_type') == 'out_invoice' and 
                vals.get('name', '/') == '/'):
                
                existing = self.search([
                    ('move_type', '=', 'out_invoice'),
                    ('name', 'like', 'INV-%'),
                    ('name', '!=', '/')
                ])

                def extract_number(name):
                    try:
                        return int(name.replace('INV-', ''))
                    except Exception:
                        return 0

                max_num = max([extract_number(rec.name) for rec in existing], default=569)
                next_num = max_num + 1
                vals['name'] = f'INV-{next_num}'

        return super(AccountMove, self).create(vals_list)