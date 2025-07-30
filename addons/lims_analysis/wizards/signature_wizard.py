from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsSampleSignatureWizard(models.TransientModel):
    _name = 'lims.sample.signature.wizard'
    _description = 'Wizard para Firmar Muestra'

    analysis_id = fields.Many2one(
        'lims.analysis',
        string='Análisis',
        required=True
    )
    
    sample_code = fields.Char(
        string='Código de Muestra',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Parámetros a Marcar',
        readonly=True
    )
    
    signature_name = fields.Char(
        string='Nombre del Firmante',
        required=True
    )
    
    signature_position = fields.Char(
        string='Cargo',
        required=True,
        default='Analista'
    )
    
    digital_signature = fields.Binary(
        string='Firma Digital',
        required=True
    )

    def action_confirm_signature(self):
        """Confirmar la firma"""
        if not self.digital_signature:
            raise UserError('Debe proporcionar una firma digital.')
        
        signature_data = {
            'signature_name': self.signature_name,
            'signature_position': self.signature_position,
            'digital_signature': self.digital_signature
        }
        
        self.analysis_id.confirm_sample_signature(signature_data)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Muestra Firmada',
                'message': f'La muestra {self.sample_code} ha sido firmada exitosamente.',
                'type': 'success',
            }
        }