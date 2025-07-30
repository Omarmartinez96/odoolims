from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsRevisionRequestWizard(models.TransientModel):
    _name = 'lims.revision.request.wizard'
    _description = 'Wizard para Solicitar Revisión'

    analysis_id = fields.Many2one(
        'lims.analysis',
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
    
    requested_by = fields.Char(
        string='Solicitado por',
        required=True,
        help='Nombre del cliente o persona que solicita la revisión'
    )
    
    reason = fields.Text(
        string='Motivo de la Revisión',
        required=True,
        help='Describa detalladamente por qué se solicita la revisión'
    )

    def action_create_revision(self):
        """Crear la revisión"""
        revision_data = {
            'requested_by': self.requested_by,
            'reason': self.reason
        }
        
        revision = self.analysis_id.create_revision(revision_data)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lims.analysis',
            'res_id': revision.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit'
            }
        }