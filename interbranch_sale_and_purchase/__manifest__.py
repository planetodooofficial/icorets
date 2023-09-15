{
    'name': 'InterBranch Sale and Purchase',
    'version': '1.0',
    'summary': 'accounting',
    'sequence': -100,
    'description': """ InterBranch Sale and Purchase """,
    'category': 'Productivity',
    'website': 'https://planet-odoo.com',
    'depends': ['base', 'sale', 'purchase'],
    'license': 'LGPL-3',
    'application': True,
    'data': [
                'views/inherit_sale_view.xml',
                'views/inherit_purchase_view.xml',
             ],
    'website': 'https://planet-odoo.com/',
    'installable': True,
    'auto_install': False,

}
