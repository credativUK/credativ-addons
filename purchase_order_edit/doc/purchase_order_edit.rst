Purchase Order Edit Module
+++++++++++++++++++++++++++

The module allows Purchase Orders (PO) which are in progress to be edited by the user.

This will allow any unreceived products to be decrease or removed, and other products added or increased.


1 Overview
**********

==============
Purchase Order
==============

POs create pickings and stock moves when they are confirmed. They may also be linked to sale order (SO) make to order (MTO) procurements, where the procurements workflow depends on the PO workflow so these procurements need to be transferred if possible.

Any done stock moves must be in the edited order since they represent stock which is already received. Unline the SO editing, available stock moves can be removed since incoming shipments are always available for POs.

=======================
Sale Order Procurements
=======================

Procurements which are linked to the PO by default will follow the standard workflow of a cancelled PO where the procurements become cancelled and the SOs put into exception state requiring manual correction.

The module procurement_sale_allocation allows reallocation of procurements between POs and the helper module procurement_sale_allocation_edit maintains compatability with PO editing by attempting to move all procurement allocations from the origional PO to the edited PO.

If there is no room for the procurements then they will be set back to make to stock or make to order based on the procurement method set in the SO, which may trigger the creation of a new draft PO.

2 User Guide
************

============
User Actions
============

It will be possible to do the following during an PO edit

* Add additional PO lines

* Increase the quantity of any PO line

* Remove PO lines for which the stock move is not done

* Decrease the quantity of PO lines to at least the quantity present in the done stock moves

============
Instructions
============

Any PO which is currently in progress can be edited by selecting "Edit Order" from the "More" drop down box

A new quotation PO will be created based on the PO being edited where the order lines can freely be edited.

When editing is completed the quotation can be confirmed which will make the edited PO the active PO with the following workflow:

1) Is the original PO still in progress and can be edited? If not show error

2) Are all PO lines present for done stock moves? If not show error

3) Create all new stock moves and pickings for the edited order

4) Move all done stock moves and pickings from the original PO to the edited PO

5) Remove any duplicated stock moves and pickings which are replaced by the moved objects in the previous step

6) Cancel all remaining stock moves and picking from the original PO

7) Cancel the original PO


3 Technical Guide
*****************

============
Installation
============

Install the module purchase_order_edit

This depends on the helper modules base_order_edit and purchase_edit_utils, other modules also depend on this so it may already be installed

========
Removing
========

Uninstall the module purchase_order_edit

The module base_order_edit can also be removed as long as no other modules depend on it

Any PO which is in the process of being edited should have their edited quotation PO cancelled. Confirming this would result in a duplicated PO, the original PO would no longer be cancelled


4 Testing
*********

1) Edit increasing a confirmed order with available stock

   a) Create and confirm a new PO for product A for quantity 5

   b) Verify incoming stock level for product A is 5

   c) Edit an confirm the edited PO after changing product A to quantity 10

   d) Verify incoming stock level for product A is 10

   e) Verify all stock moves for the original PO are cancelled, and the PO is cancelled

   f) Verify the edited PO has a stock move for 10 of product A, and the PO is confirmed

2) Edit decreasing a confirmed order with available stock

   a) Create and confirm a new PO for product B for quantity 10

   b) Verify incoming stock level for product B is 10

   c) Edit an confirm the edited PO after changing product B to quantity 5

   d) Verify incoming stock level for product B is 5

   e) Verify all stock moves for the original PO are cancelled, and the PO is cancelled

   f) Verify the edited PO has a stock move for 5 of product B, and the PO is confirmed

3) Edit increasing a confirmed order with done stock

   a) Create and confirm a new PO for product C for quantity 10

   b) Receive 4 of the stock

   c) Edit an confirm the edited PO after changing product C to quantity 20

   d) Verify incoming stock level for product C is 20

   e) Verify all stock moves for the original PO are cancelled, and the PO is cancelled

   f) Verify the edited PO has 2 stock moves:

      - One done for quantity 4 for product C

      - One available for quantity 16 for product C

4) Edit decreasing a confirmed order with done stock

   a) Create and confirm a new PO for product D for quantity 10

   b) Receive 4 of the stock

   c) Edit an confirm the edited PO after changing product D to quantity 3

   d) The confirmation should display an error and not let you continue

   e) Verify the edited PO is still in the quotation (draft) state

   f) Verify the original PO has not been changed

   g) Change the quantity of product D to 6 and confirm

   h) Verify all stock moves for the original PO are cancelled, and the PO is cancelled

   i) Verify the edited PO has 2 stock moves:

      - One done for quantity 4 for product D

      - One available for quantity 2 for product D

5 Troubleshooting
*****************

1) Unable to confirm an edited PO "should be in progress"

   a) Please check that the original PO is still in progress and has not recently become done or cancelled. If another user has edited the order at the same time this may have caused it to become cancelled.

2) I have made a mistake while editing an PO, but not yet confirmed it

   a) To quickly restore the edited PO to the original SO, delete the edit quotation PO and re-edit the original PO.

3) I have made a mistake while editing an PO, and have confirmed it

   a) It would be necessary to re-edit the new PO to make the correction. It is possible that stock allocations have been lost due to this edit so these may require manual actions on the stock moves and procurements to fix.

4) I need to remove a PO line which has a done stock move

   a) It is not possible to cancel or delete a done stock move from the system so this cannot be done. The PO will have to include this and manual corrections should be made in the form of additional stock moves in the reverse direction and manual corrections to the average price if applicable.

5) After editing an PO one of the allocated procurements is no longer allocated

   a) Check that the module procurement_sale_allocation_edit is installed which provides the functionality to re-allocate procurements after an edit. If this is installed then there may no logner be room in the PO for this procurement if the quantity was decreased.
