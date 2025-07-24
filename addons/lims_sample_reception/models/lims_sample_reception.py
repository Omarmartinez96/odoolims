from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class LimsSampleReception(models.Model):
    _name = 'lims.sample.reception'
    _description = 'Recepción de Muestras'
    _rec_name = 'sample_code'
    _order = 'reception_date desc, create_date desc'

    # En models/lims_sample_reception.py, después de los campos existentes:
    parameter_ids = fields.One2many(
        related='sample_id.parameter_ids',
        string='Parámetros de la Muestra',
        readonly=False
)

    # Relación con la muestra original
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True,
        ondelete='cascade'
    )
    
    # Información heredada de la muestra
    sample_identifier = fields.Char(
        string='Identificación Original',
        related='sample_id.sample_identifier',
        readonly=True
    )
    custody_chain_id = fields.Many2one(
        'lims.custody_chain',
        string='Cadena de Custodia',
        related='sample_id.custody_chain_id',
        readonly=True
    )
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sample_id.cliente_id',
        readonly=True
    )
    
    # 🆕 CÓDIGO DE MUESTRA GENERADO
    sample_code = fields.Char(
        string='Código de Muestra',
        copy=False,
        default='/',
        help='Se genera automáticamente: ABC-000/XXXX'
    )
    
    # 🆕 FECHA Y HORA DE RECEPCIÓN
    reception_date = fields.Date(
        string='Fecha de Recepción',
        default=fields.Date.context_today,
        required=True
    )
    reception_time = fields.Char(
        string='Hora de Recepción',
        placeholder='HH:MM',
        help='Formato: HH:MM (ej: 14:30)'
    )
    
    # 🆕 CHECKLIST DE RECEPCIÓN
    
    check_conditions = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La muestra está en buenas condiciones?')
    
    check_temperature = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La temperatura de recepción es adecuada?')
    
    check_container = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El recipiente está íntegro y es el adecuado para el tipo de muestra?')
    
    check_volume = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El volumen/cantidad es suficiente?')
    
    check_preservation = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿Las condiciones de preservación son correctas?')
        
    # Campos de observaciones cuando la respuesta es NO
    conditions_notes = fields.Text(
        string='Observaciones - Condiciones',
        invisible=True
    )
    can_process_conditions = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    temperature_notes = fields.Text(
        string='Observaciones - Temperatura',
        invisible=True
    )
    can_process_temperature = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    container_notes = fields.Text(
        string='Observaciones - Recipiente',
        invisible=True
    )
    can_process_container = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    volume_notes = fields.Text(
        string='Observaciones - Volumen',
        invisible=True
    )
    can_process_volume = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    preservation_notes = fields.Text(
        string='Observaciones - Preservación',
        invisible=True
    )
    can_process_preservation = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    # 🆕 ESTADOS DE RECEPCIÓN
    reception_state = fields.Selection([
        ('no_recibida', 'No Recibida'),
        ('rechazada', 'Rechazada'),
        ('recibida', 'Recibida')
    ], string='Estado de Recepción', default='no_recibida')
    
    # Campo computado para habilitar cambio de estado
    can_change_state = fields.Boolean(
        string='Puede cambiar estado',
        compute='_compute_can_change_state',
        store=True
    )
    
    # Observaciones
    reception_notes = fields.Text(
        string='Observaciones de Recepción'
    )
    # Observaciones internas de recepción
    internal_reception_notes = fields.Text(
        string='Observaciones Internas de Recepción',
        help='Notas internas del laboratorio sobre la recepción'
    )

    # Técnico que recibe
    received_by = fields.Many2one(
        'res.users',
        string='Recibido por',
        default=lambda self: self.env.user
    )
    
    @api.depends('check_conditions', 'check_temperature', 
                'check_container', 'check_volume', 'check_preservation')
    def _compute_can_change_state(self):
        """Permite cambiar estado solo si TODOS los checks están completados"""
        for record in self:
            checks = [
                record.check_conditions,
                record.check_temperature,
                record.check_container,
                record.check_volume,
                record.check_preservation
            ]
            # Todos los checks deben tener una respuesta (no estar vacíos)
            all_answered = all(check for check in checks)
            record.can_change_state = all_answered
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar código de muestra automáticamente o continuar secuencia"""
        for vals in vals_list:
            if not vals.get('sample_code') or vals.get('sample_code') == '/':
                sample = self.env['lims.sample'].browse(vals.get('sample_id'))
                if sample and sample.cliente_id:
                    client_code = sample.cliente_id.client_code or 'XXX'
                    
                    # Buscar TODOS los códigos existentes para este cliente
                    existing = self.search([
                        ('sample_code', 'like', f'{client_code}/%'),
                        ('sample_code', '!=', '/')
                    ])
                    
                    # Extraer el mayor número consecutivo existente
                    def extract_number(code):
                        try:
                            # Formato: ABC/0001
                            parts = code.split('/')
                            if len(parts) == 2:
                                return int(parts[1])
                            return 0
                        except (ValueError, IndexError):
                            return 0
                    
                    # Encontrar el número más alto
                    all_numbers = [extract_number(rec.sample_code) for rec in existing]
                    max_num = max(all_numbers) if all_numbers else 0
                    
                    # El siguiente consecutivo con 4 dígitos
                    next_num = str(max_num + 1).zfill(4)
                    vals['sample_code'] = f'{client_code}/{next_num}'
        
        return super().create(vals_list)
    
    @api.constrains('sample_code')
    def _check_unique_sample_code(self):
        """Validar que el código de muestra sea único"""
        for record in self:
            if record.sample_code and record.sample_code != '/':
                duplicate = self.search([
                    ('sample_code', '=', record.sample_code),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise UserError(f'El código de muestra "{record.sample_code}" ya existe. Debe ser único.')
                
    @api.onchange('check_conditions')
    def _onchange_check_conditions(self):
        if self.check_conditions != 'no':
            self.conditions_notes = False
            self.can_process_conditions = False

    @api.onchange('check_temperature')
    def _onchange_check_temperature(self):
        if self.check_temperature != 'no':
            self.temperature_notes = False
            self.can_process_temperature = False

    @api.onchange('check_container')
    def _onchange_check_container(self):
        if self.check_container != 'no':
            self.container_notes = False
            self.can_process_container = False

    @api.onchange('check_volume')
    def _onchange_check_volume(self):
        if self.check_volume != 'no':
            self.volume_notes = False
            self.can_process_volume = False

    @api.onchange('check_preservation')
    def _onchange_check_preservation(self):
        if self.check_preservation != 'no':
            self.preservation_notes = False
            self.can_process_preservation = False

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            template = self.template_id
            # SOLO campos esenciales para recepción
            self.name = template.name
            self.method = template.method
            self.category = template.category
            self.microorganism = template.microorganism
            self.unit = template.unit

class LimsSample(models.Model):
    _inherit = 'lims.sample'
    
    def action_create_reception(self):
        """Crear o abrir recepción para esta muestra"""
        # Buscar si ya existe una recepción para esta muestra
        reception = self.env['lims.sample.reception'].search([
            ('sample_id', '=', self.id)
        ], limit=1)
        
        if reception:
            # Si ya existe, abrir la existente
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recepción de Muestra',
                'res_model': 'lims.sample.reception',
                'res_id': reception.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Crear nueva recepción
            new_reception = self.env['lims.sample.reception'].create({
                'sample_id': self.id,
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recepción de Muestra',
                'res_model': 'lims.sample.reception',
                'res_id': new_reception.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
    # En models/lims_sample_reception.py, al final de la clase LimsSample:

    sample_reception_state = fields.Char(
        string='Estado Recepción',
        compute='_compute_sample_reception_state'
    )

    def _compute_sample_reception_state(self):
        """Mostrar estado de recepción de la muestra"""
        for record in self:
            reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', record.id)
            ], limit=1)
            
            if reception:
                states = {
                    'draft': 'Borrador',
                    'pending': 'Pendiente', 
                    'done': 'Finalizado'
                }
                record.sample_reception_state = states.get(reception.reception_state, 'Sin estado')
            else:
                record.sample_reception_state = 'No recibida'