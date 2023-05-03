# -*- coding: utf-8 -*-
#############################################################################
#
#   Adrian Gonzalalez Padron.
#   agonzalezpa0191@gmail.com
#   
#
#############################################################################

{
    'name': 'Tropipay Payment Gateway',
    'category': 'Accounting/Payment Acquirers',
    'version': '1.2.0.0.0',
    'description': """Tropipay Payment Gateway V1.2""",
    'Summary': """Tropipay Payment Gateway V1.2""",
    'author': "Adrian Gonzalez",
    'company': 'Dargoz Group',
    'maintainer': 'Adrian Gonzalez',
    'website': "https://www.dargoz.com",
    'depends': ['payment', 'account', 'website', 'website_sale'],
    'data': [
        'views/payment_template.xml',
        'views/payment_tpp_templates.xml',
        #'views/tpp_payment_template.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
