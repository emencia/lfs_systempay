# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from itsdangerous import URLSafeSerializer

from lfs.plugins import PaymentMethodProcessor
from lfs.payment.settings import PM_ORDER_IMMEDIATELY


class SystempayPaymentMethodProcessor(PaymentMethodProcessor):
    """
        Payment processor for Systempay: https://paiement.systempay.fr/html/
    """
    payment_count = 1
    payment_first_percent = 100
    payment_period = 30

    def process(self):
        if not self.order:
            return {'accepted': False,
                    'message': _('It was not possibe to process your request. Possibly your session has expired.')}

        return {
            "accepted": True,
            "next_url": self.get_relative_pay_link()
        }

    def get_create_order_time(self):
        return PM_ORDER_IMMEDIATELY

    def get_relative_pay_link(self):
        first = self.order.price * self.payment_first_percent / 100.0
        count = self.payment_count
        period = self.payment_period

        s = URLSafeSerializer(settings.SECRET_KEY)
        payment_config = s.dumps({'first': first, 'count': count, 'period': period})

        return reverse('systempay-wait-for-redirect', kwargs={'order_id': self.order.pk,
                                                              'payment_config': payment_config})

    def get_pay_link(self):
        site = Site.objects.get_current()
        rel_link = self.get_relative_pay_link()
        return 'http://%s%s' % (site.domain, rel_link)


class SystempayMultiTwicePaymentMethodProcessor(SystempayPaymentMethodProcessor):
    payment_count = 2
    payment_first_percent = 50
    payment_period = 30