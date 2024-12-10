CREATE OR REPLACE PACKAGE PKG_CUSTOMER AS
  PROCEDURE UPDATE_CUSTOMER_BALANCE(p_customer_id NUMBER, p_amount NUMBER);
  PROCEDURE SET_CUSTOMER_STATUS(p_customer_id NUMBER, p_status VARCHAR2);
END PKG_CUSTOMER;
/
CREATE OR REPLACE PACKAGE BODY PKG_CUSTOMER AS
  PROCEDURE UPDATE_CUSTOMER_BALANCE(p_customer_id NUMBER, p_amount NUMBER) IS
    l_old_balance NUMBER;
  BEGIN
    SELECT BALANCE INTO l_old_balance FROM CUSTOMERS WHERE CUSTOMER_ID = p_customer_id FOR UPDATE;
    UPDATE CUSTOMERS SET BALANCE = l_old_balance + p_amount, LAST_UPDATED_DATE = SYSDATE WHERE CUSTOMER_ID = p_customer_id;
    PKG_UTILS.LOG_MESSAGE('Updated Customer ' || p_customer_id || ' balance by ' || p_amount || ', new balance: ' || (l_old_balance + p_amount));
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      PKG_UTILS.RAISE_ERROR('Customer ' || p_customer_id || ' not found while updating balance');
  END UPDATE_CUSTOMER_BALANCE;

  PROCEDURE SET_CUSTOMER_STATUS(p_customer_id NUMBER, p_status VARCHAR2) IS
  BEGIN
    UPDATE CUSTOMERS SET CUSTOMER_STATUS = p_status, LAST_UPDATED_DATE = SYSDATE WHERE CUSTOMER_ID = p_customer_id;
    IF SQL%ROWCOUNT = 0 THEN
      PKG_UTILS.RAISE_ERROR('Customer ' || p_customer_id || ' not found to update status');
    END IF;
    PKG_UTILS.LOG_MESSAGE('Set Customer ' || p_customer_id || ' status to ' || p_status);
  END SET_CUSTOMER_STATUS;
END PKG_CUSTOMER;
/
