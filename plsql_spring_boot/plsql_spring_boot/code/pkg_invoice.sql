CREATE OR REPLACE PACKAGE PKG_INVOICE AS
  PROCEDURE CREATE_INVOICE_FOR_ORDER(p_order_id NUMBER);
  PROCEDURE ADD_INVOICE_LINE(p_invoice_id NUMBER, p_product_id NUMBER, p_quantity NUMBER, p_unit_price NUMBER);
  PROCEDURE FINALIZE_INVOICE(p_invoice_id NUMBER);
END PKG_INVOICE;
/
CREATE OR REPLACE PACKAGE BODY PKG_INVOICE AS
  PROCEDURE CREATE_INVOICE_FOR_ORDER(p_order_id NUMBER) IS
    l_invoice_id NUMBER;
    l_order_total NUMBER;
  BEGIN
    SELECT ORDER_TOTAL INTO l_order_total FROM ORDERS WHERE ORDER_ID = p_order_id;
    l_invoice_id := SEQ_INVOICE_ID.NEXTVAL;

    INSERT INTO INVOICES (INVOICE_ID, ORDER_ID, INVOICE_DATE, TOTAL_AMOUNT, CREATED_DATE, LAST_UPDATED_DATE)
    VALUES (l_invoice_id, p_order_id, SYSDATE, 0, SYSDATE, SYSDATE);

    PKG_UTILS.LOG_MESSAGE('Created Invoice ' || l_invoice_id || ' for Order ' || p_order_id);
  END CREATE_INVOICE_FOR_ORDER;

  PROCEDURE ADD_INVOICE_LINE(p_invoice_id NUMBER, p_product_id NUMBER, p_quantity NUMBER, p_unit_price NUMBER) IS
    l_line_total NUMBER;
    l_invoice_total NUMBER;
  BEGIN
    l_line_total := p_quantity * p_unit_price;
    INSERT INTO INVOICE_LINES (INVOICE_LINE_ID, INVOICE_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, LINE_TOTAL, CREATED_DATE, LAST_UPDATED_DATE)
    VALUES (SEQ_INVOICE_LINE_ID.NEXTVAL, p_invoice_id, p_product_id, p_quantity, p_unit_price, l_line_total, SYSDATE, SYSDATE);

    SELECT SUM(LINE_TOTAL) INTO l_invoice_total FROM INVOICE_LINES WHERE INVOICE_ID = p_invoice_id;

    UPDATE INVOICES SET TOTAL_AMOUNT = l_invoice_total, LAST_UPDATED_DATE = SYSDATE WHERE INVOICE_ID = p_invoice_id;

    PKG_UTILS.LOG_MESSAGE('Added invoice line to Invoice ' || p_invoice_id || ' for Product ' || p_product_id || ', QTY ' || p_quantity);
  END ADD_INVOICE_LINE;

  PROCEDURE FINALIZE_INVOICE(p_invoice_id NUMBER) IS
    l_total_amount NUMBER;
    l_order_id NUMBER;
  BEGIN
    SELECT TOTAL_AMOUNT, ORDER_ID INTO l_total_amount, l_order_id FROM INVOICES WHERE INVOICE_ID = p_invoice_id;

    UPDATE INVOICES SET LAST_UPDATED_DATE = SYSDATE WHERE INVOICE_ID = p_invoice_id;

    PKG_UTILS.LOG_MESSAGE('Finalized Invoice ' || p_invoice_id || ' for Order ' || l_order_id || ' total ' || PKG_UTILS.FORMAT_CURRENCY(l_total_amount));
  END FINALIZE_INVOICE;
END PKG_INVOICE;
/