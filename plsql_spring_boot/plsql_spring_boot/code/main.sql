-- Example scenario using these procedures:
DECLARE
  v_order_id NUMBER;
BEGIN
  -- Create a new order for customer 1
  PKG_ORDER_PROCESSING.CREATE_ORDER(1, v_order_id);
  -- Add items
  PKG_ORDER_PROCESSING.ADD_ORDER_ITEM(v_order_id, 1, 10); -- 10 units of PRODUCT_ID=1
  PKG_ORDER_PROCESSING.ADD_ORDER_ITEM(v_order_id, 2, 5);  -- 5 units of PRODUCT_ID=2

  -- Validate order
  PKG_ORDER_PROCESSING.VALIDATE_ORDER(v_order_id);

  -- Process order (reserves inventory, creates invoice, updates customer balance)
  PKG_ORDER_PROCESSING.PROCESS_ORDER(v_order_id);

  -- Ship the order
  PKG_ORDER_PROCESSING.SHIP_ORDER(v_order_id);

  -- Complete the order
  PKG_ORDER_PROCESSING.COMPLETE_ORDER(v_order_id);

  COMMIT;
END;
/
