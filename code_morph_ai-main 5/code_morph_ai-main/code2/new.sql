CREATE OR REPLACE PROCEDURE addCustomer_library(auxCustomerId IN NUMBER, auxName IN VARCHAR2, auxCustomerAddress IN VARCHAR2, auxPhone IN NUMBER,
auxPass IN VARCHAR2, auxUserName IN VARCHAR2, auxCardNumber IN NUMBER)
IS
BEGIN
  INSERT INTO customer
  VALUES (auxCustomerId,auxName,auxCustomerAddress,auxPhone,auxPass,auxUserName,sysdate,auxCardNumber);
END;

SET SERVEROUTPUT ON;
DECLARE
  auxCustomerId NUMBER;
  auxName VARCHAR2(20);
  auxCustomerAddress VARCHAR2(20);
  auxPhone NUMBER;
  auxCardNumber NUMBER;
BEGIN
  auxCustomerId := &Customer_ID;
  auxName := &Name;
  auxCustomerAddress := &Address;
  auxPhone := &Phone;
  auxPass := &Password;
  auxUserName := &User_Name;
  auxCardNumber := &Card_Numeber;
  addCustomer_library(auxCustomerId,auxName,auxCustomerAddress,auxPhone,auxPass,auxUserName,auxCardNumber);
END;