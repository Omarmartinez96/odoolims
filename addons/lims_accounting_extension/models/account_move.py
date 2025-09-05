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
                
                # Buscar todas las facturas existentes con formato INV-XXX
                existing = self.search([
                    ('move_type', '=', 'out_invoice'),
                    ('name', 'like', 'INV-%'),
                    ('name', '!=', '/')
                ])

                # Obtener el mayor consecutivo existente
                def extract_number(name):
                    try:
                        return int(name.replace('INV-', ''))
                    except Exception:
                        return 0

                max_num = max([extract_number(rec.name) for rec in existing], default=0)
                next_num = str(max_num + 1).zfill(3)
                vals['name'] = f'INV-{next_num}'

        return super(AccountMove, self).create(vals_list)