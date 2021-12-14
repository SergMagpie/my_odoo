{
    "name": "Product quantity update",
    "author": "Simbioz",
    "version": "11.0.1.0.1",
    "category": "Products",
    "depends": [
        'product',
        'sale',
        'sale_flow',
    ],
    "data": [
        "views/product_product.xml",
        "views/sale_order.xml",
        "views/res_config_settings.xml",
        "data/cron_update_quantities.xml",
    ],
    "license": 'AGPL-3',
    'installable': True,
    'images': [],
}
