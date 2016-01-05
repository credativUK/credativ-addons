.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Perform stock accounting when owner set
=======================================

In Odoo, owner on stock, if set, is set to mean that the stock already belongs
to the partner and does not perform any stock accounting on that stock. However
an alternative use of this functionality exists, that the stock has been
reserved/loaned to that owner and is still fully owned by the company.

This module re-enables stock accounting entries to be raised on those.

Known issues / Roadmap
======================

* The stock accounting code is not built with this in mind, therefore any bugs
  fixed in this area in stock_account will have to be fixed here as well.

Credits
=======

Contributors
------------

* Ondřej Kuzník <ondrej.kuznik@credativ.co.uk>

Maintainer
----------

This module is maintained by credativ ltd.
