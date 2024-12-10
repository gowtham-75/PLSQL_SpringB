CREATE OR REPLACE PACKAGE PKG_VALIDATIONS AS
  PROCEDURE VALIDATE_CUSTOMER(p_customer_id NUMBER);
  PROCEDURE VALIDATE_PRODUCT(p_product_id NUMBER);
  PROCEDURE VALIDATE_ORDER_STATUS_CHANGE(p_old_status VARCHAR2, p_new_status VARCHAR2);
  PROCEDURE VALIDATE_INVENTORY_AVAILABLE(p_product_id NUMBER, p_quantity NUMBER);
  PROCEDURE VALIDATE_CREDIT_LIMIT(p_customer_id NUMBER, p_order_total NUMBER);
END PKG_VALIDATIONS;
/
CREATE OR REPLACE PACKAGE BODY PKG_VALIDATIONS AS
  PROCEDURE VALIDATE_CUSTOMER(p_customer_id NUMBER) IS
    l_status       VARCHAR2(50);
  BEGIN
    SELECT CUSTOMER_STATUS INTO l_status FROM CUSTOMERS WHERE CUSTOMER_ID = p_customer_id;

    IF l_status <> 'ACTIVE' THEN
      PKG_UTILS.RAISE_ERROR('Customer ' || p_customer_id || ' is not active');
    END IF;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Customer ' || p_customer_id || ' does not exist');
  END VALIDATE_CUSTOMER;

  PROCEDURE VALIDATE_PRODUCT(p_product_id NUMBER) IS
    l_status VARCHAR2(50);
  BEGIN
    SELECT PRODUCT_STATUS INTO l_status FROM PRODUCTS WHERE PRODUCT_ID = p_product_id;

    IF l_status <> 'ACTIVE' THEN
      PKG_UTILS.RAISE_ERROR('Product ' || p_product_id || ' is not active or does not exist');
    END IF;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Product ' || p_product_id || ' does not exist');
  END VALIDATE_PRODUCT;

  PROCEDURE VALIDATE_ORDER_STATUS_CHANGE(p_old_status VARCHAR2, p_new_status VARCHAR2) IS
  BEGIN
    -- Some arbitrary logic:
    -- Allowed transitions: NEW -> PROCESSING -> SHIPPED -> COMPLETED
    -- Cancelation: NEW -> CANCELED, PROCESSING -> CANCELED only
    IF p_old_status = 'NEW' AND p_new_status NOT IN ('PROCESSING', 'CANCELED') THEN
      PKG_UTILS.RAISE_ERROR('Invalid status transition from ' || p_old_status || ' to ' || p_new_status);
    ELSIF p_old_status = 'PROCESSING' AND p_new_status NOT IN ('SHIPPED', 'CANCELED') THEN
      PKG_UTILS.RAISE_ERROR('Invalid status transition from ' || p_old_status || ' to ' || p_new_status);
    ELSIF p_old_status = 'SHIPPED' AND p_new_status NOT IN ('COMPLETED') THEN
      PKG_UTILS.RAISE_ERROR('Invalid status transition from ' || p_old_status || ' to ' || p_new_status);
    ELSIF p_old_status = 'COMPLETED' THEN
      PKG_UTILS.RAISE_ERROR('Order is completed, cannot change status');
    ELSIF p_old_status = 'CANCELED' THEN
      PKG_UTILS.RAISE_ERROR('Order is canceled, cannot change status');
    END IF;
  END VALIDATE_ORDER_STATUS_CHANGE;

  PROCEDURE VALIDATE_INVENTORY_AVAILABLE(p_product_id NUMBER, p_quantity NUMBER) IS
    l_stock NUMBER;
  BEGIN
    SELECT SUM(STOCK_QUANTITY) INTO l_stock FROM INVENTORY WHERE PRODUCT_ID = p_product_id;

    IF l_stock < p_quantity THEN
      PKG_UTILS.RAISE_ERROR('Not enough inventory for product ' || p_product_id || '. Requested ' || p_quantity || ', available ' || l_stock);
    END IF;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('No inventory record found for product ' || p_product_id);
  END VALIDATE_INVENTORY_AVAILABLE;

  PROCEDURE VALIDATE_CREDIT_LIMIT(p_customer_id NUMBER, p_order_total NUMBER) IS
    l_credit_limit NUMBER;
    l_balance      NUMBER;
  BEGIN
    SELECT CREDIT_LIMIT, BALANCE INTO l_credit_limit, l_balance FROM CUSTOMERS WHERE CUSTOMER_ID = p_customer_id;

    IF (l_balance + p_order_total) > l_credit_limit THEN
      PKG_UTILS.RAISE_ERROR('Customer ' || p_customer_id || ' credit limit exceeded. Limit: ' 
         || PKG_UTILS.FORMAT_CURRENCY(l_credit_limit) || ', Current Balance: ' 
         || PKG_UTILS.FORMAT_CURRENCY(l_balance) || ', Order Total: ' 
         || PKG_UTILS.FORMAT_CURRENCY(p_order_total));
    END IF;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Customer ' || p_customer_id || ' not found for credit limit validation');
  END VALIDATE_CREDIT_LIMIT;
END PKG_VALIDATIONS;
/