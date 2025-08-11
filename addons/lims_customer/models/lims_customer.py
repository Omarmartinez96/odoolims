# lims_customer.py
from odoo import models, fields, api

class LimsCustomer(models.Model):
    _inherit = 'res.partner'

    is_lims_customer = fields.Boolean(string='Cliente LIMS', default=True)
    client_code = fields.Char(string="Código del Cliente")  # <- 🔴 SIN required=True 🔴

    # Campo computado para ordenamiento numérico
    client_code_sequence = fields.Integer(string='Secuencia de Código', compute='_compute_client_code_sequence', store=True)

    # Campos adicionales directos de res.partner (para claridad)
    vat = fields.Char(string="RFC / TAX ID")
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
                # Extraer números del código (ej: HTP-001 -> 1)
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
    
    _order = 'client_code_sequence asc, client_code asc'