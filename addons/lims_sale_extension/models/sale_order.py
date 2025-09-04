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
        
        # Marcar notas de tipo de cambio para eliminación (sin unlink)
        for line in self.order_line:
            if line.display_type == 'line_note' and 'Tipo de cambio aplicado' in (line.name or ''):
                line._origin = None  # Marcar para eliminación
        
        if self.currency_id != company_currency:
            # Convertir a moneda extranjera (USD)
            for line in self.order_line:
                if line.display_type != 'line_note' and line.product_id and hasattr(line, 'price_unit'):
                    # Siempre convertir desde el precio base del producto (en MXN)
                    line.price_unit = company_currency._convert(
                        line.product_id.list_price,
                        self.currency_id,
                        self.company_id,
                        self.date_order or fields.Date.today()
                    )
            
            # Obtener tasa para la nota
            rate = company_currency._get_conversion_rate(
                company_currency, 
                self.currency_id, 
                self.company_id, 
                self.date_order or fields.Date.today()
            )
            
            # Agregar nota como nueva línea
            inverse_rate = 1 / rate if rate > 0 else 0
            tz = pytz.timezone('America/Tijuana')
            now_tj = datetime.now(tz)
            fecha_str = now_tj.strftime('%d/%m/%Y a las %H:%M hrs')
            
            note_text = (f"Tipo de cambio aplicado: 1 USD = ${inverse_rate:.2f} MXN "
                        f"(tasa: {rate:.4f}) al {fecha_str} (Horario de Tijuana). "
                        f"Fuente: Sistema interno basado en Banco de México.")
            
            # Agregar nueva línea de nota
            self.order_line = [(0, 0, {
                'display_type': 'line_note',
                'name': note_text,
                'sequence': 999,
            })]
        else:
            # Regresar a MXN - restaurar precios originales
            for line in self.order_line:
                if line.display_type != 'line_note' and line.product_id and hasattr(line, 'price_unit'):
                    line.price_unit = line.product_id.list_price