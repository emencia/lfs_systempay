# -*- coding: utf-8 -*-
from django.core.mail.message import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from itsdangerous import URLSafeSerializer

import lfs
from lfs.checkout.settings import CHECKOUT_TYPE_AUTH
from lfs.order.models import Order
from lfs.order.settings import SUBMITTED, PAID, PAYMENT_FAILED, PAYMENT_FLAGGED
from lfs.customer import utils as customer_utils
import lfs.core.utils

from .error_codes import VADS_RESULT_CODES, VADS_EXTRA_RESULT_CODES
from .utils import prepare_systempay_form, generate_signature

# Load logger
import logging
logger = logging.getLogger("systempay")


def wait_for_redirect(request, order_id, payment_config):
    """ We have to submit special form to Systempay using POST request, in order to redirect user to Systempay pages.
        This view displays 'Wait for redirect...' page that submits hidden form automatically.

        This page might be used after user clicks order link in e-mail
    """
    s = URLSafeSerializer(settings.SECRET_KEY)
    payment_config_dict = s.loads(payment_config)

    shop = lfs.core.utils.get_default_shop()
    if request.user.is_anonymous() and \
       shop.checkout_type == CHECKOUT_TYPE_AUTH:
        return HttpResponseRedirect(reverse("lfs_checkout_login"))

    # check if this is order of current user
    customer = customer_utils.get_customer(request)

    try:
        order = Order.objects.get(pk=order_id, state__in=(SUBMITTED, PAYMENT_FAILED, PAYMENT_FLAGGED))
    except Order.DoesNotExist:
        return render(request, 'lfs_systempay/wait_for_redirect.html', {'order': None})

    if customer is None:
        raise Http404
    if order.user:
        if order.user != customer.user:
            raise Http404
    elif order.session != customer.session:
        raise Http404

    data = prepare_systempay_form(request, order, payment_config_dict['first'], payment_config_dict['count'],
                                  payment_config_dict['period'])
    data['transaction_url'] = getattr(settings, 'SYSTEMPAY_TRANSACTION_URL',
                                       'https://systempay.cyberpluspaiement.com/vads-payment/')
    data['order'] = order

    logger.info('wait_for_redirect: Prepared request for Systempay. order.id: %s, %s' % (order.pk, data))

    is_test = False
    if settings.SYSTEMPAY_MODE == 'TEST':
        is_test = True

    data['is_test'] = is_test

    return render(request, 'lfs_systempay/wait_for_redirect.html', data)


@csrf_exempt
def systempay_return_url(request, action=''):
    """
        This view is used to show return landing page for user that is redirected back from systempay to our shop.
        This view is used both in case of succes or failure of the payment (this is identified by action parameter)
    """
    logger.info('Return from Systempay. Action: %s' % action)
    return render(request, 'lfs_systempay/return_from_systempay.html', {'action': action})


@csrf_exempt
def systempay_delayed(request, uid):
    if uid != settings.SYSTEMPAY_BACK_URL_SECRET_UID:
        raise Http404
    out = handle_return_from_systempay(request, is_test=False)
    return HttpResponse('OK')

@csrf_exempt
def systempay_test_delayed(request, uid):
    if uid != settings.SYSTEMPAY_BACK_URL_SECRET_UID:
        raise Http404
    out = handle_return_from_systempay(request, is_test=True)
    return HttpResponse('OK')


def handle_return_from_systempay(request, is_test=True):
    logger.info('Call from Systempay')
    logger.debug('req.get: %s' % request.GET)
    logger.debug('req.post: %s' % request.POST)

    if request.method != 'POST':
        logger.error('Request is not POST!')
        raise Http404

    pd = request.POST

    data = {'vads_action_mode': pd.get('vads_action_mode'),
            'vads_amount': pd.get('vads_amount'),
            'vads_auth_result': pd.get('vads_auth_result'),
            'vads_auth_mode': pd.get('vads_auth_mode'),
            'vads_auth_number': pd.get('vads_auth_number'),
            'vads_capture_delay': pd.get('vads_capture_delay'),
            'vads_card_brand': pd.get('vads_card_brand'),
            'vads_card_number': pd.get('vads_card_number'),
            'vads_ctx_mode': pd.get('vads_ctx_mode'),
            'vads_currency': pd.get('vads_currency'),
            'vads_extra_result': pd.get('vads_extra_result'),
            'vads_payment_config': pd.get('vads_payment_config'),
            'signature': pd.get('signature'),
            'vads_site_id': pd.get('vads_site_id'),
            'vads_trans_date': pd.get('vads_trans_date'),
            'vads_trans_id': pd.get('vads_trans_id'),
            'vads_validation_mode': pd.get('vads_validation_mode'),
            'vads_warranty_result': pd.get('vads_warranty_result'),
            'vads_payment_certificate': pd.get('vads_payment_certificate'),
            'vads_result': pd.get('vads_result'),
            'vads_version': pd.get('vads_version'),
            'vads_order_id': pd.get('vads_order_id'),
            'vads_order_info': pd.get('vads_order_info'),
            'vads_order_info2': pd.get('vads_order_info2'),
            'vads_threeds_enrolled': pd.get('vads_threeds_enrolled'),
            'vads_threeds_cavv': pd.get('vads_threeds_cavv'),
            'vads_threeds_eci': pd.get('vads_threeds_eci'),
            'vads_threeds_xid': pd.get('vads_threeds_xid'),
            'vads_threeds_cavvAlgorithm': pd.get('vads_threeds_cavvAlgorithm'),
            'vads_threeds_status': pd.get('vads_threeds_status')
            }
    logger.info(simplejson.dumps(data))

    check_signature = generate_signature(data, is_test)

    signature_valid = data['signature'] != check_signature
    if not signature_valid:
        logger.error('Signatures do not match! Data signature: %s, check signature: %s' % (data['signature'],
                                                                                           check_signature))
        raise Http404

    out = {'status': 'SUCCESS'}
    order = None
    try:
        # get the order
        order = Order.objects.get(Q(state=SUBMITTED) | Q(state=PAYMENT_FAILED), pk=data['vads_order_info2'])
    except Order.DoesNotExist:
        try:
            logger.error((u'Systempay return url: Order does not exists: %s' % (data['vads_order_info2'])).encode('utf-8'))
        except Exception as e:
            print e
    else:
        # prepare e-mail recipients
        shop = lfs.core.utils.get_default_shop()

        from_email = shop.from_email
        to = shop.get_notification_emails()

        vads_extra_result_msg = VADS_EXTRA_RESULT_CODES.get(data['vads_extra_result'], '')
        if data['vads_result'] == '00':  # success
            order.state = PAID
            order.save()
            logger.info('sending order paid signal')
            logger.info('vads_estra_result: %s' % vads_extra_result_msg)
            lfs.core.signals.order_paid.send({"order": order, "request": request})
        else:
            out['status'] = 'ERROR'
            logger.error('Payment error: %s' % VADS_RESULT_CODES.get(data['vads_result'], '-'))
            if data['vads_result'] in ['05', '30']:
                logger.error('Extra information: %s' % vads_extra_result_msg)
            else:
                vads_extra_result_msg = ''
            order.state = PAYMENT_FAILED
            order.save()

            # prepare e-mail to shop owners
            subject = render_to_string('lfs_systempay/order_failed_subject.html')
            body = render_to_string('lfs_systempay/order_failed_body.html',
                                    {'order': order,
                                     'shop': shop,
                                     'error_message': VADS_RESULT_CODES.get(data['vads_result'], '-'),
                                     'vads_extra_result_msg': vads_extra_result_msg,
                                     'error': _('Data returned from Systempay: %s') % data})

            mail = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=to)
            mail.send(fail_silently=True)

    out['order'] = order
    out.update(data)
    return out
