from datetime import datetime
import pytz
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=False, index=True, default='/')

    client_code = fields.Char(
        string="Código del Cliente",
        related='partner_id.client_code',
        readonly=True,
        store=True
    )

    lims_branch_id = fields.Many2one(
        'lims.branch', 
        string="Sucursal",
        domain="[('customer_id', '=', partner_id)]"
    )

    lims_department_id = fields.Many2one(
        'lims.department',
        string="Departamento",
        domain="[('branch_id', '=', lims_branch_id)]"
    )

    lims_contact_ids = fields.Many2many(
        'lims.contact',
        'sale_order_lims_contact_rel',  # tabla relacional
        'order_id',                     # campo en sale.order
        'contact_id',                   # campo en lims.contact
        string="Contactos",
        domain="[('department_id', '=', lims_department_id)]"
    )

    @api.model_create_multi
    def create(self, vals_list):
        year = str(datetime.today().year)

        for vals in vals_list:
            if vals.get('name', '/') == '/':
                # Buscar todas las cotizaciones con ese año en el nombre
                existing = self.search([
                    ('name', 'like', f'%/{year}'),
                    ('name', '!=', '/')
                ])

                # Obtener el mayor consecutivo existente
                def extract_number(name):
                    try:
                        return int(name.split('/')[0])
                    except Exception:
                        return 0

                max_num = max([extract_number(rec.name) for rec in existing], default=0)
                next_num = str(max_num + 1).zfill(3)
                vals['name'] = f'{next_num}/{year}'

        return super(SaleOrder, self).create(vals_list)
    
    @api.onchange('partner_id')
    def _onchange_partner_id_currency(self):
        super()._onchange_partner_id()  # Llamar al original primero
        if self.partner_id and self.partner_id.country_id:
            if self.partner_id.country_id.code == 'US':
                usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd:
                    self.currency_id = usd

    @api.onchange('currency_id')
    def _onchange_currency_id_convert_prices(self):
        if not self.currency_id or not self.order_line:
            return
        
        # Obtener moneda de la compañía (MXN)
        company_currency = self.company_id.currency_id
        
        # Solo procesar si es diferente a la moneda de la compañía
        if self.currency_id != company_currency:
            # Convertir precios de líneas existentes
            for line in self.order_line:
                if line.display_type != 'line_note' and line.price_unit > 0:
                    # Convertir el precio actual de la línea desde MXN a la nueva moneda
                    line.price_unit = company_currency._convert(
                        line.price_unit,  # Precio actual en MXN
                        self.currency_id,  # Nueva moneda (USD)
                        self.company_id,
                        self.date_order or fields.Date.today()
                    )
            
            # Obtener tasa para mostrar en la nota
            rate = company_currency._get_conversion_rate(
                company_currency, 
                self.currency_id, 
                self.company_id, 
                self.date_order or fields.Date.today()
            )
            
            # Agregar nota informativa sobre tipo de cambio
            self._add_exchange_rate_note(rate)
        else:
            # Si regresó a MXN, eliminar nota de tipo de cambio
            existing_note = self.order_line.filtered(
                lambda l: l.display_type == 'line_note' and 'Tipo de cambio aplicado' in (l.name or '')
            )
            if existing_note:
                existing_note.unlink()

    def _add_exchange_rate_note(self, rate):
        # Buscar si ya existe una nota de tipo de cambio
        existing_note = self.order_line.filtered(
            lambda l: l.display_type == 'line_note' and 'Tipo de cambio aplicado' in (l.name or '')
        )
        
        # Si existe, eliminarla para evitar duplicados
        if existing_note:
            existing_note.unlink()
        
        # Crear nueva nota
        # Obtener fecha/hora de Tijuana
        tz = pytz.timezone('America/Tijuana')
        now_tj = datetime.now(tz)
        fecha_str = now_tj.strftime('%d/%m/%Y a las %H:%M hrs')
        
        # Calcular tasa inversa para mayor claridad
        inverse_rate = 1 / rate if rate > 0 else 0
        note_text = (f"Tipo de cambio aplicado: 1 USD = ${inverse_rate:.2f} MXN "
                    f"(tasa: {rate:.4f}) al {fecha_str} (Horario de Tijuana). "
                    f"Fuente: Sistema interno basado en Banco de México.")
        
        self.order_line = [(0, 0, {
            'display_type': 'line_note',
            'name': note_text,
            'sequence': 999,  # Al final
        })]