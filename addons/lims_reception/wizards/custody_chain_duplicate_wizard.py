from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class CustodyChainDuplicateWizard(models.TransientModel):
    _name = 'lims.custody_chain.duplicate.wizard'
    _description = 'Wizard para Duplicar Cadena de Custodia'

    custody_chain_id = fields.Many2one(
        'lims.custody_chain',
        string='Cadena de Custodia Original',
        required=True
    )
    
    samples_count = fields.Integer(
        string='Número de Muestras',
        compute='_compute_samples_info'
    )
    
    parameters_count = fields.Integer(
        string='Total de Parámetros',
        compute='_compute_samples_info'
    )
    
    @api.depends('custody_chain_id')
    def _compute_samples_info(self):
        for record in self:
            if record.custody_chain_id:
                samples = record.custody_chain_id.sample_ids
                record.samples_count = len(samples)
                record.parameters_count = sum(len(sample.parameter_ids) for sample in samples)
            else:
                record.samples_count = 0
                record.parameters_count = 0
    
    def action_confirm_duplicate(self):
        """Confirmar y proceder con el duplicado"""
        self.ensure_one()
        
        if not self.custody_chain_id:
            raise UserError(_('No se ha especificado la cadena de custodia a duplicar.'))
        
        # Proceder con el duplicado
        new_chain = self.custody_chain_id.copy()
        
        # Retornar acción para abrir la nueva cadena Y mostrar notificación
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva Cadena de Custodia'),
            'res_model': 'lims.custody_chain',
            'res_id': new_chain.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'show_notification': {
                    'type': 'success',
                    'title': _('¡Copia Generada con Éxito!'),
                    'message': _(f'Se ha creado la nueva cadena de custodia "{new_chain.custody_chain_code}". Favor de verificar que todos los campos sean correctos.'),
                }
            }
        }