# -*- coding: utf-8 -*-
#############################################################################
#
#   Adrian Gonzalalez Padron.
#   agonzalezpa0191@gmail.com
#
#
#############################################################################


from odoo import fields, models, api, _


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('tpp', "(tpp) Tropipay")],
        ondelete={'tpp': 'set default'}
    )
    client_id = fields.Char(string='ID_Cliente')
    client_secret = fields.Char(string='Cliente_Secret')

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['tpp'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res

    def _tpp_get_api_url(self):
        """ Return the API URL according to the provider state.
        Note: self.ensure_one()
        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://www.tropipay.com/api/v2/access/token'
        else:
            return 'https://tropipay-dev.herokuapp.com/api/v2/access/token'

    def _tpp_get_endpoint_url(self):
        """ Return the ENDPOINT URL according to the provider state.
        Note: self.ensure_one()
        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://www.tropipay.com/api/v2/paymentcards'
        else:
            return 'https://tropipay-dev.herokuapp.com/api/v2/paymentcards'
