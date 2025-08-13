# lims_customer.py
from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsCustomer(models.Model):
    _inherit = 'res.partner'

    # ========== CAMPOS PRINCIPALES ==========
    is_lims_customer = fields.Boolean(string='Cliente LIMS', default=True)
    client_code = fields.Char(string="Código del Cliente")
    
    # Campo almacenado para ordenamiento numérico
    client_sequence = fields.Integer(
        string='Número Consecutivo',
        compute='_compute_client_sequence',
        store=False,  # 🔧 PASO 1: Sin store temporalmente
        help='Número extraído del código cliente para ordenamiento (001, 002, etc.)'
    )

    # Campos heredados redefinidos para claridad
    vat = fields.Char(string="RFC / TAX ID", required=True)
    street = fields.Char(string="Calle y número")
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

    # ========== RELACIONES ==========
    branch_ids = fields.One2many(
        'lims.branch',
        'customer_id',
        string="Sucursales"
    )
    
    # ========== CAMPOS COMPUTADOS PARA SMART BUTTONS ==========
    branch_count = fields.Integer(string='Número de Sucursales', compute='_compute_counts')
    total_departments = fields.Integer(string='Total Departamentos', compute='_compute_counts')
    total_contacts = fields.Integer(string='Total Contactos', compute='_compute_counts')

    # ========== MÉTODOS COMPUTADOS ==========
    @api.depends('branch_ids', 'branch_ids.department_ids', 'branch_ids.department_ids.contact_ids')
    def _compute_counts(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.total_departments = sum(len(branch.department_ids) for branch in record.branch_ids)
            record.total_contacts = sum(len(dept.contact_ids) for branch in record.branch_ids for dept in branch.department_ids)

    @api.depends('client_code')
    def _compute_client_sequence(self):
        """Extraer SOLO el número consecutivo para ordenamiento"""
        for record in self:
            if record.client_code and '-' in record.client_code:
                try:
                    # Extraer número después del guión: ABC-001 -> 1
                    num_part = record.client_code.split('-')[-1]
                    record.client_sequence = int(num_part) if num_part.isdigit() else 99999
                except (ValueError, IndexError):
                    record.client_sequence = 99999
            else:
                record.client_sequence = 99999

    # ========== MÉTODOS DE CREACIÓN Y ACTUALIZACIÓN ==========
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_lims_customer'):
                # Solo generar código automáticamente si no existe pero hay RFC
                if not vals.get('client_code') and vals.get('vat'):
                    vals['client_code'] = self._generate_client_code(vals['vat'])
                # ❌ QUITADO: Ya no es obligatorio tener código
        
        return super().create(vals_list)

    def write(self, vals):
        # Si cambia el RFC y no tiene client_code, generarlo
        if vals.get('vat') and not self.client_code:
            vals['client_code'] = self._generate_client_code(vals['vat'])
        
        return super().write(vals)

    # ========== GENERACIÓN DE CÓDIGOS ==========
    def _generate_client_code(self, rfc):
        """Generar código basado en RFC: ABC123... -> ABC-001"""
        if not rfc or len(rfc) < 3:
            return False
        
        # Tomar las 3 primeras letras del RFC
        prefix = rfc[:3].upper()
        
        # Buscar el mayor consecutivo existente para este prefijo
        existing = self.env['res.partner'].search([
            ('client_code', 'like', f'{prefix}-%'),
            ('client_code', '!=', False),
            ('id', '!=', self.id)  # Excluir el registro actual
        ])
        
        # Extraer números consecutivos
        max_num = 0
        for record in existing:
            if record.client_code:
                try:
                    # Formato: ABC-001 -> extraer 001
                    parts = record.client_code.split('-')
                    if len(parts) == 2 and parts[1].isdigit():
                        num = int(parts[1])
                        max_num = max(max_num, num)
                except (ValueError, IndexError):
                    continue
        
        # Generar siguiente consecutivo
        next_num = str(max_num + 1).zfill(3)
        return f'{prefix}-{next_num}'

    # ========== ORDENAMIENTO OPTIMIZADO ==========
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Ordenamiento numérico inteligente para clientes LIMS"""
        # DEBUG: Forzar ordenamiento para clientes LIMS
        if not order and any('client_code' in str(arg) for arg in args):
            order = None  # Forzar nuestro ordenamiento personalizado
            
            # Buscar registros con ordenamiento básico
            result = super().search(args, offset=0, limit=None, order='client_code asc', count=False)
            
            if count:
                return len(result)
                
            if result:
                # Ordenar por número consecutivo
                records = self.browse(result)
                sorted_records = records.sorted(key=lambda r: (
                    int(r.client_code.split('-')[-1]) if r.client_code and '-' in r.client_code and r.client_code.split('-')[-1].isdigit() else 99999,
                    r.client_code or ''
                ))
                
                # Aplicar offset y limit
                if offset:
                    sorted_records = sorted_records[offset:]
                if limit:
                    sorted_records = sorted_records[:limit]
                    
                return sorted_records.ids
            
            return result
            
        return super().search(args, offset=offset, limit=limit, order=order, count=count)

    # ========== ACCIÓN MASIVA PARA CÓDIGOS FALTANTES ==========
    def action_view_departments(self):
        """Acción para ver departamentos (placeholder)"""
        return True

    def action_view_contacts(self):
        """Acción para ver contactos (placeholder)"""
        return True

    # ========== ACCIÓN MASIVA PARA CÓDIGOS FALTANTES ==========
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
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin Cambios',
                    'message': 'Todos los clientes ya tienen código asignado.',
                    'type': 'info'
                }
            }