CREATE OR REPLACE PACKAGE PKG_INVENTORY AS
  PROCEDURE RESERVE_INVENTORY(p_product_id NUMBER, p_quantity NUMBER);
  PROCEDURE RELEASE_INVENTORY(p_product_id NUMBER, p_quantity NUMBER);
  PROCEDURE DECREMENT_INVENTORY(p_product_id NUMBER, p_quantity NUMBER);
  PROCEDURE INCREMENT_INVENTORY(p_product_id NUMBER, p_quantity NUMBER);
END PKG_INVENTORY;
/
CREATE OR REPLACE PACKAGE BODY PKG_INVENTORY AS
  PROCEDURE RESERVE_INVENTORY(p_product_id NUMBER, p_quantity NUMBER) IS
    l_total_stock NUMBER;
    l_warehouse_id NUMBER;
  BEGIN
    SELECT WAREHOUSE_ID, STOCK_QUANTITY INTO l_warehouse_id, l_total_stock
      FROM (SELECT WAREHOUSE_ID, STOCK_QUANTITY FROM INVENTORY WHERE PRODUCT_ID = p_product_id ORDER BY STOCK_QUANTITY DESC)
      WHERE ROWNUM = 1;

    IF l_total_stock < p_quantity THEN
      PKG_UTILS.RAISE_ERROR('Cannot reserve inventory. Insufficient stock for product ' || p_product_id);
    END IF;

    UPDATE INVENTORY
      SET STOCK_QUANTITY = STOCK_QUANTITY - p_quantity,
          LAST_UPDATED_DATE = SYSDATE
      WHERE PRODUCT_ID = p_product_id
        AND WAREHOUSE_ID = l_warehouse_id
        AND STOCK_QUANTITY >= p_quantity;

    IF SQL%ROWCOUNT = 0 THEN
      PKG_UTILS.RAISE_ERROR('Failed to reserve inventory for product ' || p_product_id);
    END IF;
    
    PKG_UTILS.LOG_MESSAGE('Reserved ' || p_quantity || ' units of product ' || p_product_id || ' from warehouse ' || l_warehouse_id);
  END RESERVE_INVENTORY;

  PROCEDURE RELEASE_INVENTORY(p_product_id NUMBER, p_quantity NUMBER) IS
    l_warehouse_id NUMBER;
  BEGIN
    -- For simplicity, just put released inventory back into a default warehouse (lowest id)
    SELECT MIN(WAREHOUSE_ID) INTO l_warehouse_id FROM INVENTORY WHERE PRODUCT_ID = p_product_id;

    UPDATE INVENTORY
      SET STOCK_QUANTITY = STOCK_QUANTITY + p_quantity,
          LAST_UPDATED_DATE = SYSDATE
      WHERE PRODUCT_ID = p_product_id
        AND WAREHOUSE_ID = l_warehouse_id;

    IF SQL%ROWCOUNT = 0 THEN
      -- If no inventory record existed, create one
      INSERT INTO INVENTORY (PRODUCT_ID, WAREHOUSE_ID, STOCK_QUANTITY, REORDER_LEVEL, LAST_UPDATED_DATE)
      VALUES (p_product_id, l_warehouse_id, p_quantity, 100, SYSDATE);
    END IF;

    PKG_UTILS.LOG_MESSAGE('Released ' || p_quantity || ' units of product ' || p_product_id || ' back into warehouse ' || l_warehouse_id);
  END RELEASE_INVENTORY;

  PROCEDURE DECREMENT_INVENTORY(p_product_id NUMBER, p_quantity NUMBER) IS
    -- This could be similar to reserve, but we assume at this point inventory is already set aside
    l_warehouse_id NUMBER;
  BEGIN
    SELECT WAREHOUSE_ID INTO l_warehouse_id FROM INVENTORY WHERE PRODUCT_ID = p_product_id AND STOCK_QUANTITY >= p_quantity AND ROWNUM = 1;
    UPDATE INVENTORY
      SET STOCK_QUANTITY = STOCK_QUANTITY - p_quantity,
          LAST_UPDATED_DATE = SYSDATE
      WHERE PRODUCT_ID = p_product_id
        AND WAREHOUSE_ID = l_warehouse_id;
        
    IF SQL%ROWCOUNT = 0 THEN
      PKG_UTILS.RAISE_ERROR('Failed to decrement inventory for product ' || p_product_id);
    END IF;

    PKG_UTILS.LOG_MESSAGE('Permanently decremented inventory of product ' || p_product_id || ' by ' || p_quantity);
  END DECREMENT_INVENTORY;

  PROCEDURE INCREMENT_INVENTORY(p_product_id NUMBER, p_quantity NUMBER) IS
    l_warehouse_id NUMBER;
  BEGIN
    -- Just pick a warehouse (lowest id)
    SELECT MIN(WAREHOUSE_ID) INTO l_warehouse_id FROM INVENTORY WHERE PRODUCT_ID = p_product_id;
    UPDATE INVENTORY
      SET STOCK_QUANTITY = STOCK_QUANTITY + p_quantity,
          LAST_UPDATED_DATE = SYSDATE
      WHERE PRODUCT_ID = p_product_id AND WAREHOUSE_ID = l_warehouse_id;

    IF SQL%ROWCOUNT = 0 THEN
      INSERT INTO INVENTORY (PRODUCT_ID, WAREHOUSE_ID, STOCK_QUANTITY, REORDER_LEVEL, LAST_UPDATED_DATE)
      VALUES (p_product_id, l_warehouse_id, p_quantity, 100, SYSDATE);
    END IF;

    PKG_UTILS.LOG_MESSAGE('Incremented inventory of product ' || p_product_id || ' by ' || p_quantity);
  END INCREMENT_INVENTORY;
END PKG_INVENTORY;
/