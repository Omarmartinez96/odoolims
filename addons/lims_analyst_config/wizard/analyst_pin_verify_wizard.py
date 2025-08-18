from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

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
            'verified_by_user': self.env.user.id,
            'verification_datetime': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ PIN Verificado',
                'message': f'Identidad verificada correctamente para {self.analyst_id.full_name}',
                'type': 'success',
                'sticky': False,
            }
        }