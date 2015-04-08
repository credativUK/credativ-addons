Procurement Sale Allocation Module
++++++++++++++++++++++++++++++++++

The module allows procurements to be switched between the Make To Stock (MTS) and Make To Order (MTO) workflow by changing the Purchase Order (PO) a procurement is linked to.

This will allow the procurement to attempt to allocate to available stock or, if linked to a PO, to be made available when the PO has arrived.


1 Overview
**********

==========================
Make To Stock Procurements
==========================

The standard MTS procurement workflow will attempt to allocate stock moves from available stock. If no stock is available the procurement will remain in exception until stock becomes available. Usually re-ordering rules will trigger the creation of new POs.

When a procurement is changed to no longer be linked to a PO the workflow will be changed to MTS and will attempt to allocate to available stock. If no stock is available it will change to an exception state and follow the standard workflow.

==========================
Make To Order Procurements
==========================

The standard MTO procurement workflow will trigger the creation of a new Request For Quotation (RFQ), a draft PO. For each procurement a new PO line will be created which is linked back to that procurement. Once the PO has arrived and that PO line is received, the linked procurement and it's stock move is moved to available.

When a procurement is changed to be linked to a PO, the following workflow will be applied:

* Does the PO have free space for this procurement? ie PO lines with enough quantity which are not allocated to other procurements.
* Is this PO allowed to have allocations currently? eg if the PO is frozen as it is due to arrive at the warehouse then allocations cannot be changed
* Split the PO line with available quantity into a new PO line linked to this procurement
* The procurement workflow will be changed to MTO and linked to the PO workflow which will move it to the running state as per the standard workflow.

When a procurement is changed to no longer be linked to a PO, the following workflow will be applied in addition to the steps in the MTS section:

* Is this PO allowed to have de-allocations currently? eg if the PO is frozen as it is due to arrive at the warehouse then allocations cannot be changed
* The PO line linked to this procurement will be freed up for allocation and merged into any other free PO lines for this PO


2 User Guide
************

============
User Actions
============

By modifying the PO which is linked to a procurement the following actions are made possible:

* MTS to MTO
* MTO to MTS
* MTO to MTO (allocating to a different PO)

============
Instructions
============

To view the currently linked PO to a procurement, navigate to the menu "Warehouse/Schedulers/Procurement Exceptions", clear all filters and search for the procurement you need to change.

In the form view of the procurement the field "Purchase Order" will show the currently assigned PO. This field can be changed on an exception which is not done or cancelled.

In the form view of the PO under the Procurements tab a new list field is displayed showing all procurements allocated to this PO and all order lines which are free to allocate to other procurements.

When changing the PO allocation of a procurement a note will be logged below to indicate the change which took place, including: PO references, user, timestamp.


3 Technical Guide
*****************

============
Installation
============

Install the module procurement_sale_allocation

========
Removing
========

Uninstall the module procurement_sale_allocation

The data and workflows are always kept consistent with the core procurement module so no further changes are required to remove

=======
Testing
=======

1) MTS to MTO

   a) Create and confirm a new PO with MTS product A with quantity 10

   b) Create and confirm a new SO with MTS product A with quantity 4

   c) Verify the procurement for the SO is MTS and in exception

   d) Change the PO on the procurement to the PO in the first step

   e) Verify the PO has two lines of 4 and 6, the first allocated to the procurement

   f) Fully receive the PO

   g) Verify the stock for the SO is now available

2) MTO to MTS

   a) Create and confirm a new SO with MTO product B with quantity 5

   b) Run the procurement scheduler

   c) Verify a new RFQ is created for product B quantity 5 and confirm

   d) Change the PO on the procurement to be empty

   e) Verify the PO now has one free line for 5 not allocated to the procurement

   f) Fully receive the PO

   g) Verify the stock for the SO is still confirmed

   h) Run the procurement scheduler

   i) Verify the stock for the SO is now available

3) MTO to MTO

   a) Create and confirm a new PO (PO1) with MTO product C with quantity 10

   b) Create and confirm a new SO with MTO product C with quantity 8

   c) Run the procurement scheduler

   d) Verify a new RFQ (PO2) is created for product C quantity 8 and confirm

   e) Change the PO on the procurement from PO2 to PO1

   f) Verify PO1 has two lines of 8 and 2, the first allocated to the procurement

   g) Verify PO2 now has one free line for 8 not allocated to the procurement

   h) Fully receive PO2

   i) Verify the stock for the SO is still confirmed

   j) Fully receive PO1

   k) Verify the stock for the SO is now available


5 Troubleshooting
*****************

1) A stock move has been cancelled but it's procurement which is linked to a PO is still running.

   a) This is the standard behaviour of OpenERP as a MTO procurement will not be cancelled unless the PO it is linked to is cancelled. The normal workflow would cause any stock received which is linked to this procurement to just become available to other procurements, then the procurement will be changed to cancelled. This module would allow to PO to be unset on the procurement which would cause the procurement to move to the cancelled state.

2) A procurement has been linked to a PO however no PO lines have been allocated to the procurement.

   a) This would be caused in the case where the procurement is either done or cancelled. There would be no need to allocate any PO lines to a procurement in this state so it is not done. This could happen in a race condition where the procurement became done at the same time as it was allocated to a PO by a user.

3) A procurement cannot be linked to a PO, not enough space:

   a) Please confirm that the PO has an unallocated PO line for the same product, for at least the same quantity, and going to the same warehouse and location.

4) A procurement cannot be linked or unlinked to a PO, not allowed to allocate:

   a) The PO has been frozen and can no longer be changed in any way. This could indicate a situation where the final version of the PO details have been confirmed with the warehouse and changes made in OpenERP will no longer have any affect so are restricted.

5) Cancelling a PO no longer puts MTO sale orders for this PO in shipping exception as per the standard OpenERP workflow:

   a) Once a PO has been cancelled or deleted all linked procurements will be moved automatically to the MTS workflow which will keep the sale orders in a normal state. It will be possible to manually, or with the procurement_sale_allocation_scheduler module, automatically link the procurements to new POs otherwise the procurements will remain in exception state until there is available stock.
