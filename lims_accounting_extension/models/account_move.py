from datetime import datetime
import json
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
        """Descargar PDF del complemento de pago (representación impresa CFDI)"""
        self.ensure_one()
        # invoice_payments_widget es el mismo JSON que Odoo usa para mostrar
        # los pagos en la cabecera de la factura — si Odoo lo muestra, está aquí
        widget_raw = self.invoice_payments_widget
        if not widget_raw or widget_raw == 'false':
            raise UserError(_('No se encontraron pagos registrados para esta factura.'))
        widget_data = json.loads(widget_raw) if isinstance(widget_raw, (str, bytes)) else widget_raw
        content = (widget_data or {}).get('content', [])
        payment_ids = list({
            item.get('account_payment_id') or item.get('payment_id')
            for item in content
            if item.get('account_payment_id') or item.get('payment_id')
        })
        if not payment_ids:
            raise UserError(_('No se encontraron pagos registrados para esta factura.'))
        payments = self.env['account.payment'].browse(payment_ids).filtered(
            lambda p: p.state == 'posted'
        )
        if not payments:
            raise UserError(_('No se encontraron pagos registrados para esta factura.'))
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