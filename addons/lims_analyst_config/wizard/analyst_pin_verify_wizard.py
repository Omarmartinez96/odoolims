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
        
        return {'type': 'ir.actions.act_window_close'}