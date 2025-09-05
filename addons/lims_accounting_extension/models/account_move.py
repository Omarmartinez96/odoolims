from datetime import datetime
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    name = fields.Char(string='Número', required=True, copy=False, readonly=False, index=True, default='/')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Solo aplicar a facturas de cliente sin nombre asignado
            if (vals.get('move_type') == 'out_invoice' and 
                vals.get('name', '/') == '/'):
                
                # Buscar facturas con formato INV-XXX únicamente
                existing = self.search([
                    ('move_type', '=', 'out_invoice'),
                    ('name', 'like', 'INV-%'),
                    ('name', '!=', '/')
                ])

                # Extraer números del formato: INV-XXX
                def extract_number(name):
                    try:
                        return int(name.replace('INV-', ''))
                    except Exception:
                        return 0

                # Obtener el mayor número existente, mínimo 569 (para que próximo sea 570)
                max_num = max([extract_number(rec.name) for rec in existing], default=569)
                next_num = max_num + 1
                vals['name'] = f'INV-{next_num}'

        return super(AccountMove, self).create(vals_list)