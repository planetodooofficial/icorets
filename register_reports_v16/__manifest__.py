
{
    'name': 'Accounting Reports',
    'version': '14.0',
    'summary': 'Accounting Reports',
    'description': 'Partner Ledger Report',
    'author': 'Planet Odoo',
    'maintainer': 'Planetodoo',
    'company': 'PlanetOdoo',
    'website': 'https://planet-odoo.com/',
    'depends': ['base','account_reports','account'],
    'category': 'Accounting',
    'demo': [],
    'data': [
            'views/partner_ledger_views.xml',
            'views/ledger_confirmation.xml',
            'security/ir.model.access.csv',

             ],
    'installable': True,
    'images': ['static/description/logo'],
    'qweb': [],
    'assets': { 'web.assets_backend': [
            'register_reports_v16/static/src/css/style.css',]

    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
