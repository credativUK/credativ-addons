Sale Order Edit Module
++++++++++++++++++++++

The module allows Sale Orders (SO) which are in progress to be edited by the user.

This will allow any unshipped products to be decrease or removed, and other products added or increased.


1 Overview
**********

==========
Sale Order
==========

SOs create pickings, stock moves and procurements when they are confirmed. The procurements can trigger various operations such as purchasing and manufacturing. As well as this, the state of the stock moves and pickings need to be taken into consideration so done and available stock moves are not removed.

Any done stock moves must be in the edited order since they represent stock which is already shipped. Available stock moves must also be included since they could be pending imminent shipping, for these to be removed they should be reverted to the confirmed state by having their availability cancelled by the warehouse team.

===============
Purchase Orders
===============

Removing an item from an SO which is MTO and is linked to a Request For Quotation (RFQ) or Purchase Order (PO) will not cause them to be cancelled. If the item is present in the edited order a new MO RFQ will be created.

====================
Manufacturing Orders
====================

Removing an item from an SO which is MTO and is linked to a Manufacturing Order (MO) will result in the MO being cancelled if not yet started. If the item is present in the edited order a new MO will be created.


2 User Guide
************

============
User Actions
============

It will be possible to do the following during an SO edit

* Add additional SO lines

* Increase the quantity of any SO line

* Remove SO lines for which the stock move is not available or done

* Decrease the quantity of SO lines to at least the quantity present in the available or done stock moves

============
Instructions
============

Any SO which is currently in progress can be edited by selecting "Edit Order" from the "More" drop down box

A new quotation SO will be created based on the SO being edited where the order lines can freely be edited.

When editing is completed the quotation can be confirmed which will make the edited SO the active SO with the following workflow:

1) Is the original SO still in progress and can be edited? If not show error

2) Are all SO lines present for available and done stock moves? If not show error

3) Create all new stock moves, pickings and procurements for the edited order

4) Move all available and done stock moves, pickings and procurements from the original SO to the edited SO

5) Remove any duplicated stock moves, pickings and procurements which are replaced by the moved objects in the previous step

6) Cancel all remaining stock moves, picking and procurements from the original SO

7) If the original SO invoiced

   a) Unreconcile all payments for the original SO invoice

   b) Create a credit note for the original SO invoice

   c) Reconcile the original SO invoice and credit note

   d) Create a new invoice for the edited SO

   e) Reconcile all payments to the new invoice, which may result in an outstanding balance or an overpaid amount depending on the nature of the edit.

8) Cancel the original SO


3 Technical Guide
*****************

============
Installation
============

Install the module sale_order_edit

This depends on the helper module base_order_edit, other modules also depend on this so it may already be installed

The module order_edit is a deprecated version of this module and should not be installed

========
Removing
========

Uninstall the module sale_order_edit

The module base_order_edit can also be removed as long as no other modules depend on it

Any SO which is in the process of being edited should have their edited quotation SO cancelled. Confirming this would result in a duplicated SO, the original SO would no longer be cancelled


4 Testing
*********

1) Edit increasing a confirmed order with confirmed stock

   a) Create and confirm a new SO for product A for quantity 5

   b) Verify outgoing stock level for product A is 5

   c) Edit an confirm the edited SO after changing product A to quantity 10

   d) Verify outgoing stock level for product A is 10

   e) Verify all stock moves for the original SO are cancelled, and the SO is cancelled

   f) Verify the edited SO has a stock move for 10 of product A, and the SO is confirmed

2) Edit decreasing a confirmed order with confirmed stock

   a) Create and confirm a new SO for product B for quantity 10

   b) Verify outgoing stock level for product B is 10

   c) Edit an confirm the edited SO after changing product B to quantity 5

   d) Verify outgoing stock level for product B is 5

   e) Verify all stock moves for the original SO are cancelled, and the SO is cancelled

   f) Verify the edited SO has a stock move for 5 of product B, and the SO is confirmed

3) Edit increasing a confirmed order with available stock

   a) Create and confirm a new SO for product C for quantity 5

   b) Force availability of the stock move for the SO

   c) Edit an confirm the edited SO after changing product C to quantity 10

   d) Verify outgoing stock level for product C is 10

   e) Verify all stock moves for the original SO are cancelled, and the SO is cancelled

   f) Verify the edited SO has 2 stock moves:

      - One available for quantity 5 for product C

      - One confirmed for quantity 5 for product C

4) Edit decreasing a confirmed order with available stock

   a) Create and confirm a new SO for product D for quantity 10

   b) Force availability of the stock move for the SO

   c) Edit an confirm the edited SO after changing product D to quantity 5

   d) The confirmation should display an error and not let you continue

   e) Verify the edited SO is still in the quotation (draft) state

   f) Verify the original SO has not been changed

5) Edit decreasing a confirmed order with part done stock

   a) Create and confirm a new SO for product E for quantity 10

   b) Force availability of the stock move for the SO

   c) Process the stock move to delivery only 4

   d) Cancel the availability of the created backorder for 6

   e) Edit an confirm the edited SO after changing product E to quantity 3

   f) The confirmation should display an error and not let you continue

   g) Change the quantity of product E to 6 and confirm

   h) Verify all stock moves for the original SO are cancelled, and the SO is cancelled

   i) Verify the edited SO has 2 stock moves:

      - One done for quantity 4 for product E

      - One confirmed for quantity 2 for product E


5 Troubleshooting
*****************

1) Unable to confirm an edited SO "should be in progress"

   a) Please check that the original SO is still in progress and has not recently become done or cancelled. If another user has edited the order at the same time this may have caused it to become cancelled.

2) I have made a mistake while editing an SO, but not yet confirmed it

   a) To quickly restore the edited SO to the original SO, delete the edit quotation SO and re-edit the original SO.

3) I have made a mistake while editing an SO, and have confirmed it

   a) It would be necessary to re-edit the new SO to make the correction. It is possible that stock allocations have been lost due to this edit so these may require manual actions on the stock moves and procurements to fix.

4) I need to remove an SO line which has an available stock move, and the warehouse has confirmed it is not going to ship

   a) Since the warehouse has confirmed this stock move will not ship it will be safe to cancel the availability of this stock move to revert it to the confirmed state. It will now be possible to remove this SO line. Other modules, such as connector_bots, may restrict cancelling the availability of stock moves, check the instructions for these modules if there is a change to the procedure.

5) After editing an SO, one of the lines which was not edited for a Make To Order (MTO) product has cause it to create a duplicate RFQ

   a) This is a known limitation of the module and this duplicate RFQ should be handled manually. This will not affect Make To Stock (MTS) products. This issue is fixed when using the procurement_sale_allocation module in conjunction with the bridge module procurement_sale_allocation_edit.
