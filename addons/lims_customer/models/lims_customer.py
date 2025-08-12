# lims_customer.py
from odoo import models, fields, api

class LimsCustomer(models.Model):
    _inherit = 'res.partner'

    is_lims_customer = fields.Boolean(string='Cliente LIMS', default=True)
    client_code = fields.Char(string="Código del Cliente")

    # Campo computado para ordenamiento numérico (CON STORE)
    client_code_sequence = fields.Integer(
        string='Secuencia de Código', 
        compute='_compute_client_code_sequence', 
    )

    # Campos adicionales directos de res.partner (para claridad)
    vat = fields.Char(string="RFC / TAX ID", required=True)
    street = fields.Char(string="Calle y número ")
    street2 = fields.Char(string="Calle 2")
    city = fields.Char(string="Ciudad")
    state_id = fields.Many2one('res.country.state', string="Estado")
    zip = fields.Char(string="Código Postal")
    country_id = fields.Many2one('res.country', string="País")
    phone = fields.Char(string="Teléfono")
    email = fields.Char(string="Email")
    company_type = fields.Selection(
        [('person', 'Individual'), ('company', 'Compañía')],
        string="Tipo de Compañía",
        default='company'
    )

    branch_ids = fields.One2many(
        'lims.branch',
        'customer_id',
        string="Sucursales"
    )
    branch_count = fields.Integer(string='Número de Sucursales', compute='_compute_counts')
    total_departments = fields.Integer(string='Total Departamentos', compute='_compute_counts')
    total_contacts = fields.Integer(string='Total Contactos', compute='_compute_counts')

    @api.depends('branch_ids', 'branch_ids.department_ids', 'branch_ids.department_ids.contact_ids')
    def _compute_counts(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.total_departments = sum(len(branch.department_ids) for branch in record.branch_ids)
            record.total_contacts = sum(len(dept.contact_ids) for branch in record.branch_ids for dept in branch.department_ids)

    @api.depends('client_code')
    def _compute_client_code_sequence(self):
        import re
        for record in self:
            if record.client_code:
                # Extraer números del código (ej: LMP-001 -> 1)
                numbers = re.findall(r'\d+', record.client_code)
                if numbers:
                    # Tomar el último número encontrado (generalmente el consecutivo)
                    record.client_code_sequence = int(numbers[-1])
                else:
                    record.client_code_sequence = 9999  # Al final si no tiene números
            else:
                record.client_code_sequence = 9999  # Al final si no tiene código

    def action_view_departments(self):
        """Método dummy para botón de departamentos"""
        return True

    def action_view_contacts(self):
        """Método dummy para botón de contactos"""
        return True
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_lims_customer') and not vals.get('client_code') and vals.get('vat'):
                vals['client_code'] = self._generate_client_code(vals['vat'])
        
        return super().create(vals_list)

    def write(self, vals):
        # Si cambia el RFC y no tiene client_code, generarlo
        if vals.get('vat') and not self.client_code:
            vals['client_code'] = self._generate_client_code(vals['vat'])
        
        return super().write(vals)

    def _generate_client_code(self, rfc):
        """Generar código basado en RFC: ABC123... -> ABC-001"""
        if not rfc or len(rfc) < 3:
            return False
        
        # Tomar las 3 primeras letras del RFC
        prefix = rfc[:3].upper()
        
        # Buscar el mayor consecutivo existente para este prefijo
        existing = self.search([
            ('client_code', 'like', f'{prefix}-%'),
            ('client_code', '!=', False)
        ])
        
        # Extraer números consecutivos
        max_num = 0
        for record in existing:
            if record.client_code:
                try:
                    # Formato: ABC-001 -> extraer 001
                    parts = record.client_code.split('-')
                    if len(parts) == 2:
                        num = int(parts[1])
                        max_num = max(max_num, num)
                except (ValueError, IndexError):
                    continue
        
        # Generar siguiente consecutivo
        next_num = str(max_num + 1).zfill(3)
        return f'{prefix}-{next_num}'
    
    def action_generate_missing_codes(self):
        """Generar códigos para clientes que no los tengan"""
        clients_without_code = self.search([
            ('is_lims_customer', '=', True),
            ('client_code', '=', False),
            ('vat', '!=', False)
        ])
        
        generated = 0
        for client in clients_without_code:
            if client.vat:
                client.client_code = client._generate_client_code(client.vat)
                generated += 1
        
        if generated > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Códigos Generados',
                    'message': f'Se generaron {generated} códigos de cliente automáticamente.',
                    'type': 'success'
                }
            }