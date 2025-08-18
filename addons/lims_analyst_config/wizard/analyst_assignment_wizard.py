from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AnalystAssignmentWizard(models.TransientModel):
    _name = 'analyst.assignment.wizard'
    _description = 'Wizard Universal para Asignar Analistas con PIN'

    # Información del registro origen
    source_model = fields.Char(
        string='Modelo Origen',
        required=True,
        help='Ej: lims.custody_chain'
    )
    
    source_record_id = fields.Integer(
        string='ID del Registro',
        required=True
    )
    
    source_field = fields.Char(
        string='Campo Destino',
        required=True,
        help='Ej: analyst_id'
    )
    
    action_description = fields.Char(
        string='Descripción de la Acción',
        default='Asignar analista',
        help='Ej: Finalizar cadena de custodia'
    )
    
    # Selección del analista
    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Seleccionar Analista',
        required=True,
        domain=[('active', '=', True), ('pin_hash', '!=', False)],
        help='Solo se muestran analistas activos con PIN configurado'
    )
    
    # Verificación PIN
    pin_input = fields.Char(
        string='PIN de Verificación',
        required=True,
        help='Ingrese su PIN para confirmar esta acción'
    )

    def verify_and_assign(self):
        """Verificar PIN y asignar analista al campo"""
        self.ensure_one()
        
        # Verificar PIN
        if not self.analyst_id.validate_pin(self.pin_input):
            raise ValidationError("PIN incorrecto. Verifique e intente nuevamente.")
        
        # Obtener el registro origen
        source_record = self.env[self.source_model].browse(self.source_record_id)
        if not source_record.exists():
            raise ValidationError("El registro origen no existe")
        
        # Asignar analista al campo especificado
        source_record.write({
            self.source_field: self.analyst_id.id
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Analista Asignado',
                'message': f'{self.analyst_id.full_name} asignado correctamente para: {self.action_description}',
                'type': 'success',
            }
        }