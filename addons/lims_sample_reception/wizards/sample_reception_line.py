from odoo import models, fields, api

class SampleReceptionLine(models.TransientModel):
    _name = 'lims.sample.reception.line'
    _description = 'Línea de Muestra para Recepción'
    
    wizard_id = fields.Many2one(
        'lims.sample.reception.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True
    )
    
    sample_identifier = fields.Char(
        string='Identificación',
        related='sample_id.sample_identifier',
        readonly=True
    )
    
    custody_chain_code = fields.Char(
        string='Cadena de Custodia',
        related='sample_id.custody_chain_id.custody_chain_code',
        readonly=True
    )

    suggested_code = fields.Char(
        string='Código Sugerido',
        compute='_compute_suggested_code'
    )
    
    sample_code = fields.Char(
        string='Código de Muestra',
        required=False,
        help='Se genera automáticamente solo si el estado es "Recibida"'
    )
    
    @api.depends('sample_id')
    def _compute_suggested_code(self):
        for line in self:
            if line.sample_id and line.sample_id.cliente_id:
                client_code = line.sample_id.cliente_id.client_code or 'XXX'
                
                # PRIMERO: Verificar si ya existe una recepción para esta muestra
                existing_reception = self.env['lims.sample.reception'].search([
                    ('sample_id', '=', line.sample_id.id)
                ], limit=1)
                
                # Si existe recepción Y estamos en modo edición, usar el código existente
                if (existing_reception and 
                    existing_reception.sample_code and 
                    existing_reception.sample_code != '/' and
                    line.wizard_id and 
                    line.wizard_id.edit_mode):
                    
                    line.suggested_code = existing_reception.sample_code
                    # En modo edición, pre-cargar el código existente
                    if not line.sample_code:
                        line.sample_code = existing_reception.sample_code
                    return
                
                # SEGUNDO: Calcular el máximo número existente en la base de datos
                existing = self.env['lims.sample.reception'].search([
                    ('sample_code', 'like', f'{client_code}/%'),
                    ('sample_code', '!=', '/')
                ])
                
                max_num = 0
                for rec in existing:
                    try:
                        parts = rec.sample_code.split('/')
                        if len(parts) == 2:
                            num = int(parts[1])
                            if num > max_num:
                                max_num = num
                    except:
                        pass
                
                # TERCERO: Contar cuántas líneas del MISMO CLIENTE están ANTES de esta línea en el wizard
                client_lines_before = 0
                if line.wizard_id and line.wizard_id.sample_lines:
                    # Obtener todas las líneas ordenadas por ID (orden de creación)
                    all_lines = line.wizard_id.sample_lines.sorted('id')
                    
                    for other_line in all_lines:
                        # Si llegamos a la línea actual, parar
                        if other_line.id == line.id:
                            break
                        
                        # Si es del mismo cliente, contar
                        if (other_line.sample_id and 
                            other_line.sample_id.cliente_id and
                            other_line.sample_id.cliente_id.client_code == client_code):
                            client_lines_before += 1
                
                # CUARTO: Generar el código consecutivo
                next_num = str(max_num + 1 + client_lines_before).zfill(4)
                line.suggested_code = f'{client_code}/{next_num}'
                
                # NO auto-asignar código - dejar vacío por defecto
                if not line.sample_code:
                    line.sample_code = ''
            else:
                line.suggested_code = 'XXX/0001'
                if not line.sample_code:
                    line.sample_code = ''