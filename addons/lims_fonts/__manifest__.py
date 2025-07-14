# lims_fonts/__manifest__.py

{
    "name": "LIMS Fonts",
    "version": "1.0",
    "summary": "Gestion de fuentes tipográficas para LIMS",
    "author": "Omar Martinez",
    "category": "Laboratory",
    "depends": ["web"],
    "assets": {
        "web.report_assets_common": [
            "lims_fonts/static/src/fonts/DejaVuSans.ttf",
            'lims_fonts/static/src/fonts/fonts.css',
        ]
    },
    "data": [
        "views/assets.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
