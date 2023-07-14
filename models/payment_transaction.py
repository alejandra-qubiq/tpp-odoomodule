# -*- coding: utf-8 -*-
#############################################################################
#
#   TropiPay.
#   soporte@tropipay.com
#
#
#############################################################################

import hashlib
import logging
import pprint

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.http import request
# Import required libraries (make sure it is installed!)
import requests
import json
import time
import sys
from datetime import datetime

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'tpp':
            return res
        return self.execute_payment()

    def execute_payment(self):
        """Fetching data and Executing Payment"""
        endpoint_url = self.env['payment.provider'].search([('code', '=', 'tpp')])._tpp_get_endpoint_url()
        _logger.info("*****ENDPOINT ********************")
        _logger.info(endpoint_url)
        odoo_base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        sale_order = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids

        order_line = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids.order_line

        invoice_items = [
            {
                'ItemName': rec.product_id.name,
                'Quantity': int(rec.product_uom_qty),
                'UnitPrice': rec.price_unit,
            }
            for rec in order_line
        ]

        sec = self.login()
        token = sec.get('access_token', '')
        headers = {
            "Content-Type": "application/json",
            'Authorization': f'Bearer {token}'
        }
        amount = self.amount
        ahora=datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        _logger.info("Mostrando country:\n%s",
                     self.partner_id.country_id.code)
        _logger.info(f' La fecha que viene{fecha}')
        payload = {
            "reference": self.reference,
            "concept": "Compra en la web",
            "favorite": False,
            "description": "Compra de productos en la tienda en linea",
            "amount": round(amount * 100, 2),  # float(f"{self.amount}00"), #str(self.amount)+"00",
            "currency": self.currency_id.name,
            "singleUse": True,
            "reasonId": 34,
            "expirationDays": 1,
            "lang": "es",
            "urlSuccess": f"{odoo_base_url}/payment/tpp/_return_url",
            "urlFailed": f"{odoo_base_url}/payment/tpp/failed",
            #urlNotification": "https://webhook.site/bc45e9cd-5bf0-432f-994e-4f86e762788f",
            #"urlNotification": f"{odoo_base_url}/payment/tpp/call-back",
            "urlNotification": f"{odoo_base_url}/payment/tpp/_information_url",
            "serviceDate": fecha,
            "directPayment": True,
            "client": {
                "name": self.partner_name,
                "lastName": ".",
                "address": self.partner_address,
                "phone": self.partner_phone,
                "email": self.partner_email,
                "countryIso": self.partner_id.country_id.code,
                "termsAndConditions": "true"
            }
        }
        _logger.info(endpoint_url)
        _logger.info(payload)
        response = requests.post(endpoint_url, json=payload, headers=headers)
        _logger.info("La URL corta obtenid es")
        _logger.info(response)
        _logger.info(response.json())
        rendering_values = {
            'api_url': response.json()["shortUrl"],
            'payment_url': response.json()["paymentUrl"],
        }
        return rendering_values


    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Getting  payment status from tropipay"""
        #notification_data_str = notification_data.decode('utf-8')
        # Deserialize the JSON string
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'tpp' or len(tx) == 1:
            return tx
        notification_data_dict = json.loads(notification_data)
        _logger.info("asdfasf: %s", notification_data_dict)

        # Access the payment_status field
        payment_status = notification_data_dict['data']['state']
        _logger.info("payment_status: %s", payment_status)
        # payment_status = notification_data['state'] #5 cuando el pago se realizo correctamente
        _logger.info("mi clientid: %s", self.env['payment.provider'].search([('code', '=', 'tpp')]).client_id)
        clientid = self.env['payment.provider'].search([('code', '=', 'tpp')]).client_id
        clientsecret = self.env['payment.provider'].search([('code', '=', 'tpp')]).client_secret
        bankOrderCode = notification_data_dict['data']['bankOrderCode']
        originalCurrencyAmount = notification_data_dict['data']['originalCurrencyAmount']
        # Concatenar los valores
        data = "{}{}{}{}".format(bankOrderCode,clientid,clientsecret,originalCurrencyAmount)

        # Calcular la firma utilizando SHA256
        signature = hashlib.sha256(data.encode()).hexdigest()
        _logger.info("misignature: {}".format(signature))
        _logger.info("Firma remota: {}, Firma local: {}".format(notification_data_dict['data']['signaturev2'],signature))
        reference = notification_data_dict['data']['reference']
        if signature != notification_data_dict['data']['signaturev2']:
            raise ValidationError(
                "tpp: " + _(
                    "Invalid Signature %s.",
                    reference)
            )
        _logger.info("reference: %s", reference)
        tx = self.search(
            [
                ('reference', '=', reference),
                ('provider_code', '=', 'tpp')])
        if not tx:
            raise ValidationError(
                "tpp: " + _(
                    "No transaction found matching reference %s.",
                    reference)
            )
        return tx
    
    
    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'tpp':
            return
        else:
            self._set_done()

    def _handle_notification_data(self, provider_code, notification_data):

        tx = self._get_tx_from_notification_data(provider_code,
                                                 notification_data)
        tx._process_notification_data(notification_data)
        tx._execute_callback()
        return tx


    def login(self):
        base_api_url = self.env['payment.provider'].search([('code', '=', 'tpp')])._tpp_get_api_url()
        client_id = self.env['payment.provider'].search([('code', '=', 'tpp')]).client_id
        client_secret = self.env['payment.provider'].search([('code', '=', 'tpp')]).client_secret
        scope = "ALLOW_EXTERNAL_CHARGE"
        grandtype = "client_credentials"
        response = requests.post(base_api_url, json={
            "grant_type": grandtype,
            "client_id": f"{client_id}",
            "client_secret": f"{client_secret}",
            "scope": scope
        })
        data = response.json()
        _logger.info("******LOS DATOS PARA VER SI SE AUTENTICO EN TROPIPAY*****")
        _logger.info(data)
        _logger.info(base_api_url)
        _logger.info(client_id)
        _logger.info(client_secret)
        _logger.info("******FIN DE LOS DATOS *****")
        return data
