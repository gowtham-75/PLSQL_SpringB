CREATE OR REPLACE PACKAGE PKG_ORDER_PROCESSING AS
  PROCEDURE CREATE_ORDER(p_customer_id NUMBER, p_order_id OUT NUMBER);
  PROCEDURE ADD_ORDER_ITEM(p_order_id NUMBER, p_product_id NUMBER, p_quantity NUMBER);
  PROCEDURE VALIDATE_ORDER(p_order_id NUMBER);
  PROCEDURE PROCESS_ORDER(p_order_id NUMBER);
  PROCEDURE SHIP_ORDER(p_order_id NUMBER);
  PROCEDURE COMPLETE_ORDER(p_order_id NUMBER);
  PROCEDURE CANCEL_ORDER(p_order_id NUMBER);
END PKG_ORDER_PROCESSING;
/
CREATE OR REPLACE PACKAGE BODY PKG_ORDER_PROCESSING AS
  PROCEDURE CREATE_ORDER(p_customer_id NUMBER, p_order_id OUT NUMBER) IS
    l_status VARCHAR2(50) := 'NEW';
  BEGIN
    PKG_VALIDATIONS.VALIDATE_CUSTOMER(p_customer_id);

    p_order_id := SEQ_ORDER_ID.NEXTVAL;
    INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, ORDER_STATUS, ORDER_TOTAL, CREATED_DATE, LAST_UPDATED_DATE)
    VALUES (p_order_id, p_customer_id, SYSDATE, l_status, 0, SYSDATE, SYSDATE);

    PKG_UTILS.LOG_MESSAGE('Created Order ' || p_order_id || ' for Customer ' || p_customer_id || ' with status ' || l_status);
  END CREATE_ORDER;

  PROCEDURE ADD_ORDER_ITEM(p_order_id NUMBER, p_product_id NUMBER, p_quantity NUMBER) IS
    l_unit_price NUMBER;
    l_total_price NUMBER;
    l_order_status VARCHAR2(50);
    l_order_customer NUMBER;
  BEGIN
    PKG_UTILS.VALIDATE_POSITIVE_NUMBER(p_quantity, 'Quantity');
    PKG_VALIDATIONS.VALIDATE_PRODUCT(p_product_id);

    SELECT ORDER_STATUS, CUSTOMER_ID INTO l_order_status, l_order_customer FROM ORDERS WHERE ORDER_ID = p_order_id;

    IF l_order_status <> 'NEW' THEN
      PKG_UTILS.RAISE_ERROR('Cannot add items to Order ' || p_order_id || ' that is not in NEW status');
    END IF;

    SELECT PRODUCT_PRICE INTO l_unit_price FROM PRODUCTS WHERE PRODUCT_ID = p_product_id;
    l_total_price := l_unit_price * p_quantity;

    INSERT INTO ORDER_ITEMS (ORDER_ITEM_ID, ORDER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, TOTAL_PRICE, CREATED_DATE, LAST_UPDATED_DATE)
    VALUES (SEQ_ORDER_ITEM_ID.NEXTVAL, p_order_id, p_product_id, p_quantity, l_unit_price, l_total_price, SYSDATE, SYSDATE);

    -- Update the order total
    UPDATE ORDERS SET ORDER_TOTAL = ORDER_TOTAL + l_total_price, LAST_UPDATED_DATE = SYSDATE WHERE ORDER_ID = p_order_id;

    PKG_UTILS.LOG_MESSAGE('Added ' || p_quantity || ' units of Product ' || p_product_id || ' to Order ' || p_order_id || ' total now ' || PKG_UTILS.FORMAT_CURRENCY(l_total_price));
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Order ' || p_order_id || ' does not exist');
  END ADD_ORDER_ITEM;

  PROCEDURE VALIDATE_ORDER(p_order_id NUMBER) IS
    l_order_status VARCHAR2(50);
    l_customer_id NUMBER;
    l_order_total NUMBER;
  BEGIN
    SELECT ORDER_STATUS, CUSTOMER_ID, ORDER_TOTAL INTO l_order_status, l_customer_id, l_order_total FROM ORDERS WHERE ORDER_ID = p_order_id;

    IF l_order_status <> 'NEW' THEN
      PKG_UTILS.RAISE_ERROR('Order ' || p_order_id || ' not in NEW status, cannot validate');
    END IF;

    -- Validate credit
    PKG_VALIDATIONS.VALIDATE_CREDIT_LIMIT(l_customer_id, l_order_total);

    -- Validate inventory for each product
    FOR rec IN (SELECT PRODUCT_ID, QUANTITY FROM ORDER_ITEMS WHERE ORDER_ID = p_order_id) LOOP
      PKG_VALIDATIONS.VALIDATE_INVENTORY_AVAILABLE(rec.PRODUCT_ID, rec.QUANTITY);
    END LOOP;

    PKG_UTILS.LOG_MESSAGE('Order ' || p_order_id || ' validated successfully');
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Order ' || p_order_id || ' does not exist');
  END VALIDATE_ORDER;

  PROCEDURE PROCESS_ORDER(p_order_id NUMBER) IS
    l_order_status VARCHAR2(50);
    l_customer_id NUMBER;
    l_order_total NUMBER;
    l_invoice_id NUMBER;
  BEGIN
    SELECT ORDER_STATUS, CUSTOMER_ID, ORDER_TOTAL INTO l_order_status, l_customer_id, l_order_total FROM ORDERS WHERE ORDER_ID = p_order_id;

    PKG_VALIDATIONS.VALIDATE_ORDER_STATUS_CHANGE(l_order_status, 'PROCESSING');

    -- Reserve inventory
    FOR rec IN (SELECT PRODUCT_ID, QUANTITY FROM ORDER_ITEMS WHERE ORDER_ID = p_order_id) LOOP
      PKG_INVENTORY.RESERVE_INVENTORY(rec.PRODUCT_ID, rec.QUANTITY);
    END LOOP;

    -- Create invoice
    PKG_INVOICE.CREATE_INVOICE_FOR_ORDER(p_order_id);
    SELECT INVOICE_ID INTO l_invoice_id FROM INVOICES WHERE ORDER_ID = p_order_id;

    FOR rec2 IN (SELECT PRODUCT_ID, QUANTITY, UNIT_PRICE FROM ORDER_ITEMS WHERE ORDER_ID = p_order_id) LOOP
      PKG_INVOICE.ADD_INVOICE_LINE(l_invoice_id, rec2.PRODUCT_ID, rec2.QUANTITY, rec2.UNIT_PRICE);
    END LOOP;

    PKG_INVOICE.FINALIZE_INVOICE(l_invoice_id);

    -- Update order status
    UPDATE ORDERS SET ORDER_STATUS = 'PROCESSING', INVOICE_ID = l_invoice_id, LAST_UPDATED_DATE = SYSDATE WHERE ORDER_ID = p_order_id;

    -- Update customer balance
    PKG_CUSTOMER.UPDATE_CUSTOMER_BALANCE(l_customer_id, l_order_total);

    PKG_UTILS.LOG_MESSAGE('Order ' || p_order_id || ' moved to PROCESSING status');
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Order ' || p_order_id || ' does not exist or has no invoice');
  END PROCESS_ORDER;

  PROCEDURE SHIP_ORDER(p_order_id NUMBER) IS
    l_order_status VARCHAR2(50);
    l_shipment_id NUMBER;
  BEGIN
    SELECT ORDER_STATUS INTO l_order_status FROM ORDERS WHERE ORDER_ID = p_order_id;
    PKG_VALIDATIONS.VALIDATE_ORDER_STATUS_CHANGE(l_order_status, 'SHIPPED');

    -- Decrement inventory now that we are shipping
    FOR rec IN (SELECT PRODUCT_ID, QUANTITY FROM ORDER_ITEMS WHERE ORDER_ID = p_order_id) LOOP
      PKG_INVENTORY.DECREMENT_INVENTORY(rec.PRODUCT_ID, rec.QUANTITY);
    END LOOP;

    PKG_SHIPMENT.CREATE_SHIPMENT_FOR_ORDER(p_order_id);
    SELECT SHIPMENT_ID INTO l_shipment_id FROM SHIPMENTS WHERE ORDER_ID = p_order_id;

    UPDATE ORDERS SET ORDER_STATUS = 'SHIPPED', SHIPMENT_ID = l_shipment_id, LAST_UPDATED_DATE = SYSDATE WHERE ORDER_ID = p_order_id;

    PKG_UTILS.LOG_MESSAGE('Order ' || p_order_id || ' has been SHIPPED');
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Order ' || p_order_id || ' does not exist or Shipment creation failed');
  END SHIP_ORDER;

  PROCEDURE COMPLETE_ORDER(p_order_id NUMBER) IS
    l_order_status VARCHAR2(50);
  BEGIN
    SELECT ORDER_STATUS INTO l_order_status FROM ORDERS WHERE ORDER_ID = p_order_id;

    PKG_VALIDATIONS.VALIDATE_ORDER_STATUS_CHANGE(l_order_status, 'COMPLETED');

    UPDATE ORDERS SET ORDER_STATUS = 'COMPLETED', LAST_UPDATED_DATE = SYSDATE WHERE ORDER_ID = p_order_id;

    PKG_UTILS.LOG_MESSAGE('Order ' || p_order_id || ' is now COMPLETED');
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Order ' || p_order_id || ' does not exist to complete');
  END COMPLETE_ORDER;

  PROCEDURE CANCEL_ORDER(p_order_id NUMBER) IS
    l_order_status VARCHAR2(50);
    l_customer_id NUMBER;
    l_order_total NUMBER;
    l_invoice_id NUMBER;
  BEGIN
    SELECT ORDER_STATUS, CUSTOMER_ID, ORDER_TOTAL, NVL(INVOICE_ID,0) INTO l_order_status, l_customer_id, l_order_total, l_invoice_id FROM ORDERS WHERE ORDER_ID = p_order_id;

    PKG_VALIDATIONS.VALIDATE_ORDER_STATUS_CHANGE(l_order_status, 'CANCELED');

    -- Release any reserved inventory if the order was still in NEW or PROCESSING
    IF l_order_status IN ('NEW', 'PROCESSING') THEN
      FOR rec IN (SELECT PRODUCT_ID, QUANTITY FROM ORDER_ITEMS WHERE ORDER_ID = p_order_id) LOOP
        PKG_INVENTORY.RELEASE_INVENTORY(rec.PRODUCT_ID, rec.QUANTITY);
      END LOOP;
    END IF;

    -- If invoice existed but not finalized or order is processing, handle invoice reversal if needed
    IF l_invoice_id > 0 THEN
      -- In a real system we'd probably mark invoice as canceled or credit the amount back.
      UPDATE INVOICES SET TOTAL_AMOUNT = 0, LAST_UPDATED_DATE = SYSDATE WHERE INVOICE_ID = l_invoice_id;
      DELETE FROM INVOICE_LINES WHERE INVOICE_ID = l_invoice_id;
    END IF;

    -- Reverse customer balance if order was added
    IF l_order_total > 0 THEN
      PKG_CUSTOMER.UPDATE_CUSTOMER_BALANCE(l_customer_id, -l_order_total);
    END IF;

    UPDATE ORDERS SET ORDER_STATUS = 'CANCELED', LAST_UPDATED_DATE = SYSDATE WHERE ORDER_ID = p_order_id;

    PKG_UTILS.LOG_MESSAGE('Order ' || p_order_id || ' has been CANCELED');
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Order ' || p_order_id || ' does not exist to cancel');
  END CANCEL_ORDER;
END PKG_ORDER_PROCESSING;
/
