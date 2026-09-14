{
    'name': 'Vendor Registration',
    'sequence': 1,
    'version': '19.0.1.0.0',
    'author': 'Planet Odoo',
    'description': """Vendor Registration""",
    'category': 'Accounting',
    'website': '',
    'depends': [
        'base', 'account', 'portal', 'l10n_in', 'l10n_in_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/partner.xml',
        'views/bank.xml',
        'views/template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
