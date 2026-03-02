from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

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
    
    def action_download_complemento(self):
        """Descargar PDF del Recibo de Pago (representación impresa CFDI)"""
        self.ensure_one()
        payments = self.env['account.payment']

        # Intento 1: método interno que Odoo usa para mostrar pagos en la factura
        try:
            for item in self._get_reconciled_info_JSON_values():
                pid = item.get('account_payment_id') or item.get('payment_id')
                if pid:
                    p = self.env['account.payment'].browse(pid)
                    if p.exists() and p.state == 'posted':
                        payments |= p
        except Exception:
            pass

        # Intento 2: buscar por partner comercial (cubre empresa + todos sus contactos)
        if not payments:
            partner = self.partner_id.commercial_partner_id
            candidates = self.env['account.payment'].search([
                ('partner_id', 'child_of', partner.id),
                ('payment_type', '=', 'inbound'),
                ('state', '=', 'posted'),
            ], order='id desc', limit=100)
            payments = candidates.filtered(lambda p: self in p.reconciled_invoice_ids)

        if not payments:
            raise UserError(_(
                'No se encontraron pagos para esta factura.\n\n'
                'Si la factura está en "En proceso de pago", complete primero '
                'la conciliación bancaria para que el pago quede registrado.'
            ))
        return self.env.ref('account.action_report_payment_receipt').report_action(payments)

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