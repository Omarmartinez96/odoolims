from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AnalystPinWizard(models.TransientModel):
    _name = 'analyst.pin.wizard'
    _description = 'Wizard para Configurar PIN de Analista'

    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Analista',
        required=True,
        readonly=True
    )
    
    new_pin = fields.Char(
        string='Nuevo PIN',
        required=True,
        help='PIN de 4-6 dígitos'
    )
    
    confirm_pin = fields.Char(
        string='Confirmar PIN',
        required=True,
        help='Repita el PIN para confirmar'
    )

    @api.constrains('new_pin')
    def _check_pin_format(self):
        """Validar formato del PIN"""
        for record in self:
            if record.new_pin:
                if len(record.new_pin) < 4 or len(record.new_pin) > 6:
                    raise ValidationError("El PIN debe tener entre 4 y 6 dígitos")
                if not record.new_pin.isdigit():
                    raise ValidationError("El PIN solo debe contener números")

    def set_pin(self):
        """Establecer el PIN del analista"""
        self.ensure_one()
        
        # Validar que los PINs coincidan
        if self.new_pin != self.confirm_pin:
            raise ValidationError("Los PINs no coinciden. Por favor verifique.")
        
        # Establecer el PIN en el analista
        self.analyst_id.set_pin(self.new_pin)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'PIN Configurado',
                'message': f'PIN establecido correctamente para {self.analyst_id.full_name}',
                'type': 'success',
                'sticky': False,
            }
        }