from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AnalystPinVerifyWizard(models.TransientModel):
    _name = 'analyst.pin.verify.wizard'
    _description = 'Wizard para Verificar PIN de Analista'

    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Analista a Verificar',
        required=True,
        readonly=True
    )
    
    pin_input = fields.Char(
        string='PIN',
        required=True,
        help='Ingrese el PIN del analista'
    )

    def verify_pin(self):
        """Verificar el PIN del analista"""
        self.ensure_one()
        
        if not self.analyst_id.validate_pin(self.pin_input):
            raise ValidationError("PIN incorrecto. Verifique e intente nuevamente.")
        
        # Marcar como verificado
        self.analyst_id.write({
            'is_pin_verified': True,
        })
        
        # Si viene de una cadena de custodia, asignar el analista
        custody_chain_id = self.env.context.get('custody_chain_id')
        custody_chain_model = self.env.context.get('custody_chain_model')
        
        if custody_chain_id and custody_chain_model:
            custody_chain = self.env[custody_chain_model].browse(custody_chain_id)
            if custody_chain.exists():
                custody_chain.analyst_id = self.analyst_id.id
                
                # Retornar acción para refrescar la vista
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': custody_chain_model,
                    'res_id': custody_chain_id,
                    'view_mode': 'form',
                    'target': 'current',
                    'context': {
                        'notification': {
                            'type': 'success',
                            'title': '✅ PIN Verificado',
                            'message': f'Analista {self.analyst_id.full_name} asignado correctamente'
                        }
                    }
                }
        
        return {'type': 'ir.actions.act_window_close'}