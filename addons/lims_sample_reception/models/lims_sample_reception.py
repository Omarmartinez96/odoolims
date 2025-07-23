from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class LimsSampleReception(models.Model):
    _name = 'lims.sample.reception'
    _description = 'Recepción de Muestras'
    _rec_name = 'sample_code'
    _order = 'reception_date desc, create_date desc'

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
    check_identification = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La muestra está identificada correctamente?', default='na')
    
    check_conditions = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La muestra está en buenas condiciones?', default='na')
    
    check_temperature = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La temperatura de recepción es adecuada?', default='na')
    
    check_container = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El recipiente está íntegro y adecuado?', default='na')
    
    check_volume = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El volumen/cantidad es suficiente?', default='na')
    
    check_preservation = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿Las condiciones de preservación son correctas?', default='na')
    
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
    
    @api.depends('check_identification', 'check_conditions', 'check_temperature', 
                'check_container', 'check_volume', 'check_preservation')
    def _compute_can_change_state(self):
        """Permite cambiar estado solo si TODOS los checks están completados (no en 'na')"""
        for record in self:
            checks = [
                record.check_identification,
                record.check_conditions,
                record.check_temperature,
                record.check_container,
                record.check_volume,
                record.check_preservation
            ]
            # Todos los checks deben estar completados (no en 'na')
            all_completed = all(check in ['si', 'no'] for check in checks)
            record.can_change_state = all_completed
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar código de muestra automáticamente SIEMPRE"""
        for vals in vals_list:
            if not vals.get('sample_code') or vals.get('sample_code') == '/':
                sample = self.env['lims.sample'].browse(vals.get('sample_id'))
                if sample and sample.cliente_id:
                    client_code = sample.cliente_id.client_code or 'XXX'
                    
                    # Buscar el último consecutivo para este cliente
                    existing = self.search([
                        ('sample_code', 'like', f'{client_code}/%'),
                        ('sample_code', '!=', '/')
                    ])
                    
                    # Extraer el mayor consecutivo
                    def extract_number(code):
                        try:
                            # Formato: MAP/0001
                            parts = code.split('/')
                            if len(parts) == 2:
                                return int(parts[1])
                            return 0
                        except (ValueError, IndexError):
                            return 0
                    
                    max_num = max([extract_number(rec.sample_code) for rec in existing], default=0)
                    next_num = str(max_num + 1).zfill(4)  # 4 dígitos: 0001, 0002, etc.
                    vals['sample_code'] = f'{client_code}/{next_num}'
        
        return super().create(vals_list)

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