
{
    'name': 'GTS Accounting',
    'version': '16.0',
    'summary': 'GTS Sales',
    'description': 'Partner Ledger Report',
    'author': 'Geotechnosoft',
    'maintainer': 'Geotechnosoft',
    'company': 'Geotechnosoft',
    'website': 'https://planet-odoo.com/',
    'depends': ['base', 'account_reports', 'account'],
    'category': 'Accounting',
    'demo': [],
    'data': [
            'security/ir.model.access.csv',
            'data/partner_ledger.xml',
            'wizard/upload_document_view.xml',
            'views/account_move_view.xml',
            'views/account_account_view.xml',
             ],
    'installable': True,
    'images': [],
    'qweb': [],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
