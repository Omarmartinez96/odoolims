from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def _get_starting_sequence(self):
        """Personalizar secuencia inicial para facturas"""
        if self.journal_id and self.move_type == 'out_invoice':
            year = fields.Date.context_today(self).year
            # Buscar el último número de factura del año
            last_invoice = self.search([
                ('move_type', '=', 'out_invoice'),
                ('journal_id', '=', self.journal_id.id),
                ('name', 'like', f'INV-%/{year}')
            ], order='id desc', limit=1)
            
            if last_invoice and last_invoice.name:
                # Extraer número de la secuencia INV-XXX/YYYY
                try:
                    parts = last_invoice.name.split('/')
                    if len(parts) == 2 and parts[1] == str(year):
                        number_part = parts[0].replace('INV-', '')
                        next_number = int(number_part) + 1
                        return f"INV-{next_number:03d}/{year}"
                except:
                    pass
            
            # Si no hay facturas previas, empezar con 001
            return f"INV-001/{year}"
        
        return super()._get_starting_sequence()

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribir creación para aplicar numeración personalizada"""
        for vals in vals_list:
            if vals.get('move_type') == 'out_invoice' and not vals.get('name', '/') != '/':
                # Solo aplicar si no tiene nombre asignado
                journal = self.env['account.journal'].browse(vals.get('journal_id'))
                if journal:
                    year = fields.Date.context_today(self).year
                    
                    # Buscar último número
                    last_invoice = self.search([
                        ('move_type', '=', 'out_invoice'),
                        ('journal_id', '=', journal.id),
                        ('name', 'like', f'INV-%/{year}')
                    ], order='id desc', limit=1)
                    
                    next_number = 1
                    if last_invoice and last_invoice.name:
                        try:
                            parts = last_invoice.name.split('/')
                            if len(parts) == 2 and parts[1] == str(year):
                                number_part = parts[0].replace('INV-', '')
                                next_number = int(number_part) + 1
                        except:
                            pass
                    
                    vals['name'] = f"INV-{next_number:03d}/{year}"
        
        return super().create(vals_list)