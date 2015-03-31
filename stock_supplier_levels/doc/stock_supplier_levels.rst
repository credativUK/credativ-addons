Stock Supplier Levels Module
++++++++++++++++++++++++++++

The module allows stock levels to be tracked at a special supplier location which would represent the stock levels for that supplier for that particular warehouse


1 Overview
**********

=====================
Supplier Stock Levels
=====================

In the context of a warehouse configured with a supplier's stock location two new stock fields show the virtual stock only at this location, and one showing the virtual stock of both your warehouse and the supplier location combined

Stock levels can be for all suppliers or, by using a production lot linked to a particular supplier, for individual suppliers

===========
Inventories
===========

Physical inventories can be run to set the stock level at this special supplier location in the same way as any normal location

The fill inventory functionality of the inventories can be used to quickly and easily set the stock of the entire supplier location to 0.

===============
Purchase Orders
===============

To prevent race conditions when a purchase order is raised, at the same time incoming stock is created from the main supplier location, the supplier's stock location can also be reduced so the combined virtual stock level remains unchanged.



2 User Guide
************

============
User Actions
============

The following actions are available to a user in normal use:

* Inventory to set the stock level at the supplier's location, for all suppliers or for individual suppliers

* Confirming purchase orders which will automatically reduce the stock location at the supplier's stock location

============
Instructions
============

To view the supplier's stock location and also this value combined with the current virtual stock level, navigate to the "Inventory" tab of the product form view and check the section "Stock and Expected Variations"

To set the supplier's stock at this location, create a new physical inventory and add lines for this product and location.

If the stock level needs to be differentiated from another supplier's stock level for the same product a lot number (Serial Number) can be set in the inventory. The lot should have the partner set to the supplier which it represents. To keep the names unique the serial number can be entered to use a combination of product reference and supplier reference.

To set the supplier's stock location to 0 for all products, create a new physical inventory and use the "Fill Inventory" wizard and the "Set to zero" option in the supplier’s location.

To raise a purchase order which automatically reduces the stock level in the supplier’s location, set the "Reduce Supplier Stock" flag on the purchase order lines, or "Force Reduce Supplier Stock" on the purchase order to reduce the level for all purchase order lines.


3 Technical Guide
*****************

============
Installation
============

Install the module stock_supplier_levels

For each warehouse which requires a special supplier's stock location, create a new location under "Virtual" of type "Supplier". In the warehouse configuration set this location in the field "Virtual Supplier Location"

========
Removing
========

Uninnstall the module stock_supplier_levels

The special supplier's stock location will remain however will be unused. This can be deactivated if required.

=======
Testing
=======

1) Setting supplier stock level

   a) Create a physical inventory at the supplier’s stock location

   b) Set stock to 10 for product A with no serial number

   c) Verify the supplier stock level is 10 in the product form view

2) Purchase Order to reduce stock level

   a) Create and confirm a Purchase Order for 6 of product A and set to reduce supplier stock level

   b) Verify the supplier stock level is now 4, and the incoming stock level is 6 with the combined total remaining at 10

3) Purchase Order to not reduce stock level

   a) Create and confirm a Purchase Order for 20 of product A and don't set to reduce supplier stock level

   b) Verify the supplier stock level remains at 4, and the incoming stock level is 26 with the combined total remaining at 30

4) Purchase Order greater than supplier stock level

   a) Create and confirm a Purchase Order for 20 of product A and set to reduce supplier stock level

   b) Verify the supplier stock level is reduced to 0, and the incoming stock level is 46 with the combined total changing to 46

5) Setting supplier stock level per supplier

   a) Create a physical inventory at the supplier’s stock location

   b) Set stock to 10 for product B with a new serial number belonging to supplier A

   c) Set stock to 20 for product B with a new serial number belonging to supplier B

   d) Verify the supplier stock level is 30 in the product form view

6) Purchase Order to reduce supplier stock level

   a) Create and confirm a Purchase Order for supplier A for 8 of product B and set to reduce supplier stock level

   b) Verify the supplier stock level is now 22, and the incoming stock level is 8 with the combined total remaining at 30

7) Set all supplier stock to 0

   a) Create a physical inventory at the supplier’s stock location

   b) Fill inventory at the supplier’s stock location to 0

   c) Confirm and verify in the posted inventory:

      - No move is created for product A

      - A move of 2 is created for product B for the serial number of supplier A

      - A move of 20 is created for product B for the serial number of supplier B

   d) Verify the supplier stock level is now 0, and the incoming stock level is 8 with the combined total of 8


5 Troubleshooting
*****************

1) I have cancelled a purchase order which was set to reduce the supplier stock level. My stock level is now too low.

   a) When a purchase order of this type is confirmed it will reduce the supplier stock level. The additionally created incoming stock move will cause the total stock to appear the same for the combined value. When this purchase order is cancelled the incoming move is also cancelled and the supplier stock level is not automatically increased again, this should be done manually.

2) I have confirmed a purchase order which is set to reduce the supplier stock level, but the supplier stock level is 0.

   a) This is supported and the supplier stock level will not be affected as it will only be reduced to a minimum of 0.

3) I have confirmed a purchase order which is set to reduce the supplier stock level, but the supplier stock level is less than the ordered quantity.

   a) This is supported and the supplier stock will be reduced to a minimum of 0.

4) I have confirmed a purchase order which is set to reduce the supplier stock level for supplier A. Supplier B has enough stock but supplier A does not.

   a) This is supported and the supplier stock for A will be reduced to a minimum of 0. The stock level for supplier B will not be changed
