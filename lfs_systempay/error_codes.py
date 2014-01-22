# -*- coding: utf-8 -*-
VADS_RESULT_CODES = {'00': 'Payment successfully completed',
                     '02': 'The merchant must contact the holder’s bank',
                     '05': 'Payment denied',
                     '17': 'Cancellation by customer',
                     '30': 'Request format error. To be linked with the value of the vads_extra_result field',
                     '96': 'Technical error occurred during payment'}


VADS_EXTRA_RESULT_CODES = {'': 'No controls performed ',
         '00': 'All the controls have been successful',
         '02': 'Over the card authorized limit',
         '03': 'The card number appears on the merchant grey list',
         '04': 'The emission country of the card appears on the merchant grey list or the card emission country does not appear on the merchant white list.',
         '05': 'IP address appears on the merchant grey list',
         '99': 'Technical problem occurred on the server while performing local controls'
}
