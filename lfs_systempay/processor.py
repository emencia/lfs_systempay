# -*- coding: utf-8 -*-
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from lfs.plugins import PaymentMethodProcessor
from lfs.payment.settings import PM_ORDER_ACCEPTED, PM_ORDER_IMMEDIATELY


class SystempayPaymentMethodProcessor(PaymentMethodProcessor):
    """
        Payment processor for Systempay: https://paiement.systempay.fr/html/
    """
    def process(self):
        if not self.order:
            return {'accepted': False,
                    'message': _('It was not possibe to process your request. Possibly your session has expired.')}
        return {
            "accepted": True,
            "next_url": reverse('systempay-wait-for-redirect', kwargs={'order_id': self.order.pk}),
        }

    def get_create_order_time(self):
        return PM_ORDER_IMMEDIATELY

    def get_pay_link(self):
        site = Site.objects.get_current()
        return 'http://%s%s' % (site.domain, reverse('systempay-wait-for-redirect', kwargs={'order_id': self.order.pk}))