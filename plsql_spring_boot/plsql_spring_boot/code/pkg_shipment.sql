CREATE OR REPLACE PACKAGE PKG_SHIPMENT AS
  PROCEDURE CREATE_SHIPMENT_FOR_ORDER(p_order_id NUMBER);
  PROCEDURE UPDATE_SHIPMENT_STATUS(p_shipment_id NUMBER, p_new_status VARCHAR2);
  FUNCTION  GENERATE_TRACKING_NUMBER RETURN VARCHAR2;
END PKG_SHIPMENT;
/
CREATE OR REPLACE PACKAGE BODY PKG_SHIPMENT AS
  FUNCTION GENERATE_TRACKING_NUMBER RETURN VARCHAR2 IS
  BEGIN
    RETURN 'TRACK-' || TO_CHAR(SYSDATE, 'YYYYMMDDHH24MISS') || '-' || DBMS_RANDOM.STRING('U', 8);
  END GENERATE_TRACKING_NUMBER;

  PROCEDURE CREATE_SHIPMENT_FOR_ORDER(p_order_id NUMBER) IS
    l_shipment_id NUMBER;
    l_tracking VARCHAR2(200);
  BEGIN
    l_shipment_id := SEQ_SHIPMENT_ID.NEXTVAL;
    l_tracking := GENERATE_TRACKING_NUMBER();

    INSERT INTO SHIPMENTS (SHIPMENT_ID, ORDER_ID, SHIPMENT_DATE, SHIPMENT_STATUS, TRACKING_NUMBER, CREATED_DATE, LAST_UPDATED_DATE)
    VALUES (l_shipment_id, p_order_id, SYSDATE, 'PENDING', l_tracking, SYSDATE, SYSDATE);

    PKG_UTILS.LOG_MESSAGE('Created Shipment ' || l_shipment_id || ' for Order ' || p_order_id || ' Tracking: ' || l_tracking);
  END CREATE_SHIPMENT_FOR_ORDER;

  PROCEDURE UPDATE_SHIPMENT_STATUS(p_shipment_id NUMBER, p_new_status VARCHAR2) IS
  BEGIN
    UPDATE SHIPMENTS SET SHIPMENT_STATUS = p_new_status, LAST_UPDATED_DATE = SYSDATE WHERE SHIPMENT_ID = p_shipment_id;

    IF SQL%ROWCOUNT = 0 THEN
      PKG_UTILS.RAISE_ERROR('Shipment ' || p_shipment_id || ' not found');
    END IF;

    PKG_UTILS.LOG_MESSAGE('Updated Shipment ' || p_shipment_id || ' status to ' || p_new_status);
  END UPDATE_SHIPMENT_STATUS;
END PKG_SHIPMENT;
/