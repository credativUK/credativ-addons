.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================
Sage like Tax report
====================

This module implements customer receivables returns and allows to send
related reconciled account move lines back to a state where the debt is still
open, and letting history of it.

This module can be extended adding importers that automatically fills the
full returned payment record.

Usage
=====

Go to Accounting > Customers > Customer Payment Returns, and create a new
record, register on each line a paid (reconciled) receivable journal item,
and input the amount that is going to be returned.

Another option to fill info is setting references and click match button to
find matches with invoices, move lines or moves. This functionality is extended
by other modules as *account_payment_return_import_sepa_pain*

Next, press button "Confirm" to create a new move line that removes the
balance from the bank journal and reconcile items together to show payment
history through it.

Credits
=======

Contributors
------------
* Kinner Vachhani <kinner.vachhani@credativ.co.uk>
