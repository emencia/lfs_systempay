# -*- coding: utf-8 -*-
import hashlib
import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

# Load logger
import logging
from lfs_systempay.models import SystempayTransaction

logger = logging.getLogger("systempay")


def generate_signature(data, is_test):
    signature = []
    sorted_keys = sorted(data.keys())
    for key in sorted_keys:
        if key.startswith('vads_'):
            signature.append('%s' % data[key])
    if is_test:
        signature.append(getattr(settings, 'SYSTEMPAY_TEST_CERTIFICATE', ''))
    else:
        signature.append(getattr(settings, 'SYSTEMPAY_CERTIFICATE', ''))
    signature = '+'.join(signature)
    gen_sig = hashlib.sha1(signature.encode('utf-8')).hexdigest()

    logger.debug('keys: %s' % (', '.join(sorted_keys)))
    logger.debug('signature: %s' % signature)
    logger.debug('generated signature: %s' % signature)
    return gen_sig


def prepare_systempay_form(request, order):
    out = {}
    site = Site.objects.get_current()

    amount = order.price

    sys_trans = SystempayTransaction.get_next_transaction(order)

    # convert to cents
    out['vads_amount'] = '%d' % (amount * 100)
    out['vads_contrib'] = 'LFS'
    out['vads_action_mode'] = 'INTERACTIVE'
    out['vads_ctx_mode'] = getattr(settings, 'SYSTEMPAY_MODE', 'TEST')
    out['vads_currency'] = getattr(settings, 'SYSTEMPAY_CURRENCY', '978')  # 978 is EURO
    out['vads_cust_name'] = ' '.join((order.customer_firstname, order.customer_lastname))[:127]
    out['vads_cust_email'] = order.customer_email
    if order.user:
        out['vads_cust_id'] = order.user_id

    out['vads_cust_address'] = (' '.join((order.invoice_address.line1 or '', order.invoice_address.line2 or '')))[:255]
    out['vads_cust_city'] = (order.invoice_address.city or '')[:63]
    out['vads_cust_zip'] = (order.invoice_address.zip_code or '')[:63]

    out['vads_order_id'] = order.number
    out['vads_order_info'] = '[%s] %s %s' % (order.number, order.customer_firstname, order.customer_lastname)
    out['vads_order_info2'] = order.pk

    out['vads_site_id'] = getattr(settings, 'SYSTEMPAY_SITE_ID', '')

    out['vads_trans_date'] = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')

    # vads_trans_id
    # This parameter is required. It is made of 6 numeric characters and must be unique
    # for each transaction for a given shop and a given day. In fact, the transaction
    # unique identifier at the platform level is a concatenation of the vads_site_id,
    # the vads_trans_date restricted to the day value (YYYYMMDD part) and the
    # vads_trans_id. It is the responsibility of the commercial site to warrant its
    # uniqueness for the current day. It must necessarily range from 000000 to 899999.
    # The 900000 to 999999 bracket is not allowed.
    # Note: a value with a length under 6 characters generates an error when the
    # payment URL is called. Please try and abide by the 6 characters length
    #out['vads_trans_id'] = '%06d' % (order.pk - (order.pk // 899999) * 899999)
    out['vads_trans_id'] = '%06d' % sys_trans.uid

    out['vads_url_cancel'] = 'http://%s%s' % (site.domain, reverse('systempay-return-cancel-url'))
    out['vads_url_error'] = 'http://%s%s' % (site.domain, reverse('systempay-return-error-url'))
    out['vads_url_referral'] = 'http://%s%s' % (site.domain, reverse('systempay-return-referral-url'))
    out['vads_url_refused'] = 'http://%s%s' % (site.domain,  reverse('systempay-return-refused-url'))
    out['vads_url_success'] = 'http://%s%s' % (site.domain, reverse('systempay-return-success-url'))
    out['vads_url_return'] = 'http://%s%s' % (site.domain, reverse('systempay-return-url'))
    out['vads_version'] = 'V2'
    out['vads_return_mode'] = 'NONE'
    out['vads_payment_config'] = 'SINGLE'
    out['vads_payment_cards'] = ''
    out['vads_page_action'] = 'PAYMENT'

    out['signature'] = generate_signature(out, settings.SYSTEMPAY_MODE == 'TEST')

    return out
