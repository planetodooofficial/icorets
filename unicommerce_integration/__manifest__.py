{
    'name': 'Unicommerce Integration',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'summary': 'Unicommerce Integration',
    'description': """
        Unicommerce Odoo Integration
        ========================
        This module is used to integrate unicommerce with odoo sales
    """,
    'author': 'Teckzilla Technologies',
    'website': 'https://www.teckzilla.net/',
    'depends': ['base', 'sale', 'stock', 'contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/crons.xml',
        'wizard/fetch_missing_orders.xml',
        'wizard/sale_channel_report_view.xml',
        'views/unicommerce_orders_view.xml',
        'views/shop_instance_view.xml',
        'views/shop_import_logs_view.xml',
        'views/shop_channel.xml',
        'views/menu_items.xml',
        'views/sale.xml',
        'views/account.xml',
        # 'views/stock_picking.xml',
        # 'views/stock_location.xml',
        'views/contacts.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
