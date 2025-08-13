from odoo import models

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """Override para forzar opciones anti-compresión específicas para LIMS"""
        
        # Solo aplicar a reportes LIMS (que usan nuestro paperformat)
        if hasattr(self, 'paperformat_id') and self.paperformat_id:
            if 'lims' in (self.paperformat_id.name or '').lower():
                # Forzar parámetros anti-compresión
                command_args = [
                    '--disable-smart-shrinking',
                    '--zoom', '1.05',
                    '--image-quality', '100',
                    '--minimum-font-size', '10'
                ]
                
                # Aplicar al contexto para que wkhtmltopdf los use
                self = self.with_context(wkhtmltopdf_args=command_args)
        
        return super()._render_qweb_pdf(report_ref, res_ids, data)