from odoo import api, fields, models, exceptions, _
import requests
import hashlib


class ProductQuantitiesUpdate(models.Model):
    _inherit = 'product.product'

    quantity_Switzerland = fields.Float(
        string='Switzerland quantity',
        default=0,
    )
    quantity_Italy = fields.Float(
        string='Italy quantity',
        default=0,
    )
    quantity_Romania = fields.Float(
        string='Romania quantity',
        default=0,
    )
    _operation_get_token = 'getchallenge'
    _operation_get_products = 'getproducts'

    def _get_hash(self, token, key_user):
        md5_hash = hashlib.md5((token + key_user).encode('utf-8'))
        return md5_hash.hexdigest()

    def get_europe_quantities(self):
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()
        end_point_url = params.get_param('product_quantities_update.rkbbearings_end_point_url')
        user_key = params.get_param('product_quantities_update.rkbbearings_user_key')
        user = params.get_param('product_quantities_update.rkbbearings_user')
        if not user_key or not user:
            raise exceptions.Warning(_('User key and/or user is not specified'))
        try:
            response = requests.get(url=end_point_url,
                                    params={'operation': self._operation_get_token, 'username': user})
            response_to_json = response.json()
            if response_to_json['success']:
                token = response_to_json['result']['token']
                hash_string = self._get_hash(token=token, key_user=user_key)
                data = {
                    'operation': self._operation_get_products,
                    'username': user,
                    'accessKey': hash_string,
                    'extendedcode': self.name
                }
                result = requests.post(url=end_point_url, data=data)
                get_data = result.json()
                if get_data['result']['message'] is None:
                    for line in get_data['result']['dati']:
                        if line['productcode'] == self.name:
                            self.quantity_Italy = float(line['italy'])
                            self.quantity_Romania = float(line['romania'])
                            self.quantity_Switzerland = float(line['switzerland'])
                            break
                elif get_data['result']['message'] is not None:
                    raise exceptions.Warning(get_data['result']['message'])
        except Exception as exc:
            raise exceptions.Warning(exc)

    def get_europe_quantities_cron_launcher(self):
        for record in self.search([]):
            record.get_europe_quantities()
