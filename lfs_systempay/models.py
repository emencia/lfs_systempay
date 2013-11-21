import datetime

from django.db import models
from django.db.models import SET_NULL
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from lfs.order.models import Order


class SystempayTransaction(models.Model):
    order = models.ForeignKey(Order, verbose_name=_('Order'), null=True, on_delete=SET_NULL)
    uid = models.CharField(_('uid'), max_length=10, blank=True, db_index=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    created_day = models.DateField(_('Created day'))

    @classmethod
    def get_next_transaction(cls, order):
        today = datetime.date.today()
        cnt = SystempayTransaction.objects.filter(created_day=today).count()
        created = False
        trans = None

        while not created:
            cnt += 1
            trans, created = cls.objects.get_or_create(uid=cnt, created_day=today, defaults={'order': order})

        return trans

    def __unicode__(self):
        return u'%s - %s - %s' % (self.pk, self.order.number, self.uid)

    class Meta:
        verbose_name = 'Systempay Transaction'
        verbose_name_plural = 'Systempay Transaction'