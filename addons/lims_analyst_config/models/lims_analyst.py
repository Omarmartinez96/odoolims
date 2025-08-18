from odoo import models, fields, api
from odoo.exceptions import ValidationError
import hashlib
import logging

_logger = logging.getLogger(__name__)

class LimsAnalyst(models.Model):
    _name = 'lims.analyst'
    _description = 'Analistas de Laboratorio'
    _rec_name = 'full_name'
    _order = 'full_name'

    # Información básica
    full_name = fields.Char(
        string='Nombre Completo',
        required=True,
        help='Nombre completo del analista'
    )
    
    initials = fields.Char(
        string='Iniciales',
        size=5,
        help='Iniciales del analista (máximo 5 caracteres)'
    )
    
    employee_code = fields.Char(
        string='Código de Empleado',
        help='Código único del empleado'
    )
    
    # PIN de seguridad
    pin_hash = fields.Char(
        string='PIN Hash',
        help='Hash del PIN del analista'
    )
    
    # Firma digital
    signature = fields.Binary(
        string='Firma Digital',
        help='Imagen de la firma del analista'
    )
    
    signature_text = fields.Char(
        string='Firma de Texto',
        help='Firma en formato texto'
    )
    
    # Estados y configuración
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    position = fields.Char(
        string='Cargo',
        help='Posición o cargo del analista'
    )
    
    department = fields.Char(
        string='Departamento',
        help='Departamento al que pertenece'
    )
    
    # Fechas
    start_date = fields.Date(
        string='Fecha de Inicio',
        help='Fecha de inicio en el laboratorio'
    )
    
    notes = fields.Text(
        string='Notas',
        help='Notas adicionales sobre el analista'
    )

    @api.model
    def _hash_pin(self, pin):
        """Encriptar PIN usando SHA-256"""
        if not pin:
            return False
        return hashlib.sha256(pin.encode('utf-8')).hexdigest()

    def set_pin(self, pin):
        """Establecer PIN del analista"""
        if len(pin) < 4:
            raise ValidationError("El PIN debe tener al menos 4 dígitos")
        if not pin.isdigit():
            raise ValidationError("El PIN solo debe contener números")
        
        self.pin_hash = self._hash_pin(pin)
        return True

    def validate_pin(self, pin):
        """Validar PIN del analista"""
        if not self.pin_hash:
            return False
        return self.pin_hash == self._hash_pin(pin)

    @api.model
    def verify_analyst_pin(self, analyst_id, pin):
        """Método para verificar PIN vía RPC"""
        try:
            analyst = self.browse(analyst_id)
            if not analyst.exists() or not analyst.active:
                return {'success': False, 'message': 'Analista no encontrado o inactivo'}
            
            if analyst.validate_pin(pin):
                return {
                    'success': True, 
                    'message': 'PIN correcto',
                    'analyst_name': analyst.full_name
                }
            else:
                return {'success': False, 'message': 'PIN incorrecto'}
        except Exception as e:
            _logger.error(f"Error validando PIN: {e}")
            return {'success': False, 'message': 'Error en validación'}

    def name_get(self):
        """Mostrar nombre con iniciales"""
        result = []
        for record in self:
            name = record.full_name
            if record.initials:
                name += f" ({record.initials})"
            if record.employee_code:
                name += f" - {record.employee_code}"
            result.append((record.id, name))
        return result

    @api.constrains('employee_code')
    def _check_employee_code_unique(self):
        """Validar que el código de empleado sea único"""
        for record in self:
            if record.employee_code:
                existing = self.search([
                    ('employee_code', '=', record.employee_code),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(f"Ya existe un analista con el código: {record.employee_code}")
                
    def action_set_pin(self):
        """Abrir wizard para configurar PIN"""
        self.ensure_one()
        return {
            'name': 'Configurar PIN',
            'type': 'ir.actions.act_window',
            'res_model': 'analyst.pin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_analyst_id': self.id,
            }
        }