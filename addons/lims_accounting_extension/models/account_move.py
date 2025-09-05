from datetime import datetime
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    name = fields.Char(string='Número', required=True, copy=False, readonly=False, index=True, default='/')

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

                max_num = max([extract_number(rec.name) for rec in existing], default=0)
                next_num = max_num + 1
                vals['name'] = f'INV-{str(next_num).zfill(3)}'

        return super(AccountMove, self).create(vals_list)

    def write(self, vals):
        """Cuando se modifica manualmente el número, actualizar referencia"""
        result = super().write(vals)
        return result
    
    def action_open_payment_wizard(self):
        """Abrir wizard de complemento PPD con factura preseleccionada"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generar Complemento PPD',
            'res_model': 'payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_amount': self.amount_residual,
            }
        }