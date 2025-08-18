from . import models
from . import wizard

def post_init_hook(env):
    """Hook ejecutado después de la instalación"""    
    # Establecer PIN por defecto al analista demo
    demo_analyst = env.ref('lims_analyst_config.analyst_demo_admin', raise_if_not_found=False)
    if demo_analyst:
        demo_analyst.set_pin('1234')
        print(f"✓ PIN establecido para {demo_analyst.full_name}: 1234")