from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsRevisionRequestWizardV2(models.TransientModel):
    _name = 'lims.revision.request.wizard.v2'
    _description = 'Wizard para Solicitar Revisión v2'

    # ===============================================
    # === INFORMACIÓN DEL ANÁLISIS ===
    # ===============================================
    analysis_id = fields.Many2one(
        'lims.analysis.v2',
        string='Análisis',
        required=True
    )
    
    sample_code = fields.Char(
        string='Código de Muestra',
        readonly=True
    )
    
    current_revision = fields.Integer(
        string='Revisión Actual',
        readonly=True
    )
    
    # ===============================================
    # === INFORMACIÓN DE LA REVISIÓN ===
    # ===============================================
    requested_by = fields.Char(
        string='Solicitado por',
        required=True,
        help='Nombre del cliente o persona que solicita la revisión',
        default=lambda self: self.env.user.name
    )
    
    reason = fields.Text(
        string='Motivo de la Revisión',
        required=True,
        help='Describa detalladamente por qué se solicita la revisión'
    )

    # ===============================================
    # === MÉTODOS ===
    # ===============================================
    def action_create_revision(self):
        """Crear la revisión"""
        revision_data = {
            'requested_by': self.requested_by,
            'reason': self.reason
        }
        
        revision = self.analysis_id.create_revision(revision_data)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lims.analysis.v2',
            'res_id': revision.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit'
            }
        }
    
    @api.model
    def default_get(self, fields_list):
        """Establecer valores por defecto desde contexto"""
        defaults = super().default_get(fields_list)
        
        if self.env.context.get('default_analysis_id'):
            analysis = self.env['lims.analysis.v2'].browse(self.env.context['default_analysis_id'])
            defaults.update({
                'analysis_id': analysis.id,
                'sample_code': analysis.sample_code,
                'current_revision': analysis.revision_number
            })
        
        return defaults