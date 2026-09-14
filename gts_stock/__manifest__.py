{
    'name': 'GTS Stock',
    'version': '19.0.1.0.0',
    'summary': 'GTS Stock',
    'author': 'Geotechnosoft',
    'maintainer': 'Geotechnosoft',
    'company': 'Geotechnosoft',
    'website': 'https://planet-odoo.com/',
    'depends': ['base', 'stock', 'stock_account'],
    'category': 'Inventory/Inventory',
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_view.xml',
        # 'views/stock_valuation_layer_view.xml',
        'wizard/select_warehouse_wizard_view.xml',
        'wizard/update_product_details_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}

