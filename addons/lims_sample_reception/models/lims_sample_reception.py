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
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('done', 'Finalizado')
    ], string='Estado de Recepción', default='draft')
    
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
    
    # Técnico que recibe
    received_by = fields.Many2one(
        'res.users',
        string='Recibido por',
        default=lambda self: self.env.user
    )
    
    @api.depends('check_identification', 'check_conditions', 'check_temperature', 
                 'check_container', 'check_volume', 'check_preservation')
    def _compute_can_change_state(self):
        """Permite cambiar estado solo si todos los checks están en 'si' o 'na'"""
        for record in self:
            checks = [
                record.check_identification,
                record.check_conditions,
                record.check_temperature,
                record.check_container,
                record.check_volume,
                record.check_preservation
            ]
            # Puede cambiar estado si no hay ningún 'no' y al menos uno está en 'si'
            has_no = 'no' in checks
            has_si = 'si' in checks
            
            record.can_change_state = not has_no and has_si
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar código de muestra automáticamente"""
        for vals in vals_list:
            if not vals.get('sample_code') or vals.get('sample_code') == '/':
                sample = self.env['lims.sample'].browse(vals.get('sample_id'))
                if sample and sample.cliente_id:
                    client_code = sample.cliente_id.client_code or 'XXX'
                    year = str(datetime.today().year)
                    
                    # Buscar el último consecutivo para este cliente y año
                    existing = self.search([
                        ('sample_code', 'like', f'{client_code}-%/{year}'),
                        ('sample_code', '!=', '/')
                    ])
                    
                    # Extraer el mayor consecutivo
                    def extract_number(code):
                        try:
                            # Formato: ABC-001/2025
                            parts = code.split('/')
                            if len(parts) == 2:
                                number_part = parts[0].split('-')[-1]
                                return int(number_part)
                            return 0
                        except (ValueError, IndexError):
                            return 0
                    
                    max_num = max([extract_number(rec.sample_code) for rec in existing], default=0)
                    next_num = str(max_num + 1).zfill(3)
                    vals['sample_code'] = f'{client_code}-{next_num}/{year}'
        
        return super().create(vals_list)
    
    def action_set_pending(self):
        """Cambiar estado a Pendiente"""
        if not self.can_change_state:
            raise UserError(_('Complete correctamente el checklist antes de cambiar el estado.'))
        self.reception_state = 'pending'
    
    def action_set_done(self):
        """Cambiar estado a Finalizado"""
        if not self.can_change_state:
            raise UserError(_('Complete correctamente el checklist antes de finalizar.'))
        self.reception_state = 'done'
        # Actualizar estado de la muestra original
        self.sample_id.sample_state = 'in_analysis'
    
    def action_set_draft(self):
        """Regresar a Borrador"""
        self.reception_state = 'draft'


class LimsSample(models.Model):
    _inherit = 'lims.sample'
    
    # Relación con recepción
    reception_id = fields.One2one(
        'lims.sample.reception',
        'sample_id',
        string='Recepción'
    )
    
    # Campo computado para mostrar código de muestra
    sample_code = fields.Char(
        string='Código de Muestra',
        related='reception_id.sample_code',
        readonly=True
    )
    
    def action_create_reception(self):
        """Crear recepción para esta muestra"""
        if self.reception_id:
            # Si ya existe, abrir la existente
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recepción de Muestra',
                'res_model': 'lims.sample.reception',
                'res_id': self.reception_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Crear nueva recepción
            reception = self.env['lims.sample.reception'].create({
                'sample_id': self.id,
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recepción de Muestra',
                'res_model': 'lims.sample.reception',
                'res_id': reception.id,
                'view_mode': 'form',
                'target': 'current',
            }