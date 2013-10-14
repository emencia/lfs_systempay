# django imports
from django.conf.urls.defaults import *


urlpatterns = patterns('lfs_systempay.views',
    url(r'^redirect_to_processor/(?P<order_id>\d*)/$', "wait_for_redirect", name="systempay-wait-for-redirect"),
    url(r'^systempay_delayed_(?P<uid>[\w\d]+)$', 'systempay_delayed', name='systempay-delayed-0'),
    url(r'^systempay_delayed_(?P<uid>[\w\d]+)/$', 'systempay_delayed', name='systempay-delayed'),

    url(r'^systempay_test_delayed_(?P<uid>[\w\d]+)$', 'systempay_test_delayed', name='systempay-test-delayed-0'),
    url(r'^systempay_test_delayed_(?P<uid>[\w\d]+)/$', 'systempay_test_delayed', name='systempay-test-delayed'),


    url(r'^systempay_return/$', 'systempay_return_url', name='systempay-return-url', kwargs={'action': 'return'}),
    url(r'^systempay_return_cancel/$', 'systempay_return_url', name='systempay-return-cancel-url',
        kwargs={'action': 'cancel'}),
    url(r'^systempay_return_error/$', 'systempay_return_url', name='systempay-return-error-url',
        kwargs={'action': 'error'}),
    url(r'^systempay_return_referral/$', 'systempay_return_url', name='systempay-return-referral-url',
        kwargs={'action': 'referral'}),
    url(r'^systempay_return_refused/$', 'systempay_return_url', name='systempay-return-refused-url',
        kwargs={'action': 'refused'}),
    url(r'^systempay_return_success/$', 'systempay_return_url', name='systempay-return-success-url',
        kwargs={'action': 'success'}),
    url(r'^systempay_return_invalid_request/$', 'systempay_return_url', name='systempay-return-invalid_request-url',
        kwargs={'action': 'invalid_request'}),
)