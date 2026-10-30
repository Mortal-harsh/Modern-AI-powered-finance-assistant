-- ============================================================================
-- SMART EXPENSE TRACKER WITH ANALYTICS
-- Oracle PL/SQL Stored Procedures and Functions
-- ============================================================================

-- 1. ADD_TRANSACTION: Insert an income or expense transaction
CREATE OR REPLACE PROCEDURE ADD_TRANSACTION (
    p_user_id          IN  NUMBER,
    p_category_id      IN  NUMBER,
    p_transaction_type IN  VARCHAR2,
    p_expense_type     IN  VARCHAR2,
    p_amount           IN  NUMBER,
    p_transaction_date IN  DATE,
    p_payment_method   IN  VARCHAR2,
    p_description      IN  VARCHAR2,
    p_notes            IN  VARCHAR2,
    p_transaction_id   OUT NUMBER
) AS
BEGIN
    IF p_amount <= 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Transaction amount must be strictly greater than zero.');
    END IF;

    IF p_transaction_type NOT IN ('INCOME', 'EXPENSE') THEN
        RAISE_APPLICATION_ERROR(-20002, 'Invalid transaction type. Allowed: INCOME, EXPENSE.');
    END IF;

    INSERT INTO TRANSACTIONS (
        USER_ID,
        CATEGORY_ID,
        TRANSACTION_TYPE,
        EXPENSE_TYPE,
        AMOUNT,
        TRANSACTION_DATE,
        PAYMENT_METHOD,
        DESCRIPTION,
        NOTES,
        CREATED_AT,
        UPDATED_AT
    ) VALUES (
        p_user_id,
        p_category_id,
        p_transaction_type,
        NVL(p_expense_type, 'NEED'),
        ROUND(p_amount, 2),
        p_transaction_date,
        NVL(p_payment_method, 'UPI'),
        p_description,
        p_notes,
        SYSDATE,
        SYSDATE
    ) RETURNING TRANSACTION_ID INTO p_transaction_id;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END ADD_TRANSACTION;
/

-- 2. UPDATE_TRANSACTION: Update an existing transaction
CREATE OR REPLACE PROCEDURE UPDATE_TRANSACTION (
    p_transaction_id   IN NUMBER,
    p_category_id      IN NUMBER,
    p_transaction_type IN VARCHAR2,
    p_expense_type     IN VARCHAR2,
    p_amount           IN NUMBER,
    p_transaction_date IN DATE,
    p_payment_method   IN VARCHAR2,
    p_description      IN VARCHAR2,
    p_notes            IN VARCHAR2,
    p_rows_updated     OUT NUMBER
) AS
BEGIN
    IF p_amount <= 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Transaction amount must be strictly greater than zero.');
    END IF;

    IF p_transaction_type NOT IN ('INCOME', 'EXPENSE') THEN
        RAISE_APPLICATION_ERROR(-20002, 'Invalid transaction type. Allowed: INCOME, EXPENSE.');
    END IF;

    UPDATE TRANSACTIONS
    SET CATEGORY_ID      = p_category_id,
        TRANSACTION_TYPE = p_transaction_type,
        EXPENSE_TYPE     = NVL(p_expense_type, 'NEED'),
        AMOUNT           = ROUND(p_amount, 2),
        TRANSACTION_DATE = p_transaction_date,
        PAYMENT_METHOD   = NVL(p_payment_method, 'UPI'),
        DESCRIPTION      = p_description,
        NOTES            = p_notes,
        UPDATED_AT       = SYSDATE
    WHERE TRANSACTION_ID = p_transaction_id;

    p_rows_updated := SQL%ROWCOUNT;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END UPDATE_TRANSACTION;
/

-- 3. DELETE_TRANSACTION: Delete a transaction by ID
CREATE OR REPLACE PROCEDURE DELETE_TRANSACTION (
    p_transaction_id IN  NUMBER,
    p_rows_deleted   OUT NUMBER
) AS
BEGIN
    DELETE FROM TRANSACTIONS
    WHERE TRANSACTION_ID = p_transaction_id;

    p_rows_deleted := SQL%ROWCOUNT;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END DELETE_TRANSACTION;
/

-- 4. GET_TOTAL_INCOME: Function to calculate total income for selected period
CREATE OR REPLACE FUNCTION GET_TOTAL_INCOME (
    p_user_id IN NUMBER,
    p_year    IN NUMBER DEFAULT NULL,
    p_month   IN NUMBER DEFAULT NULL
) RETURN NUMBER AS
    v_total NUMBER(14, 2) := 0;
BEGIN
    SELECT NVL(SUM(AMOUNT), 0)
    INTO v_total
    FROM TRANSACTIONS
    WHERE USER_ID = p_user_id
      AND TRANSACTION_TYPE = 'INCOME'
      AND (p_year IS NULL OR EXTRACT(YEAR FROM TRANSACTION_DATE) = p_year)
      AND (p_month IS NULL OR EXTRACT(MONTH FROM TRANSACTION_DATE) = p_month);

    RETURN v_total;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END GET_TOTAL_INCOME;
/

-- 5. GET_TOTAL_EXPENSES: Function to calculate total expenses for selected period
CREATE OR REPLACE FUNCTION GET_TOTAL_EXPENSES (
    p_user_id IN NUMBER,
    p_year    IN NUMBER DEFAULT NULL,
    p_month   IN NUMBER DEFAULT NULL
) RETURN NUMBER AS
    v_total NUMBER(14, 2) := 0;
BEGIN
    SELECT NVL(SUM(AMOUNT), 0)
    INTO v_total
    FROM TRANSACTIONS
    WHERE USER_ID = p_user_id
      AND TRANSACTION_TYPE = 'EXPENSE'
      AND (p_year IS NULL OR EXTRACT(YEAR FROM TRANSACTION_DATE) = p_year)
      AND (p_month IS NULL OR EXTRACT(MONTH FROM TRANSACTION_DATE) = p_month);

    RETURN v_total;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END GET_TOTAL_EXPENSES;
/

-- 6. GET_MONTHLY_SUMMARY: Retrieve monthly income and expenses as a SYS_REFCURSOR
CREATE OR REPLACE PROCEDURE GET_MONTHLY_SUMMARY (
    p_user_id IN  NUMBER,
    p_year    IN  NUMBER DEFAULT NULL,
    p_cursor  OUT SYS_REFCURSOR
) AS
    v_target_year NUMBER := NVL(p_year, EXTRACT(YEAR FROM SYSDATE));
BEGIN
    OPEN p_cursor FOR
        WITH MONTHS AS (
            SELECT LEVEL AS M_NUM,
                   TO_CHAR(TO_DATE(LEVEL, 'MM'), 'Mon') AS M_NAME
            FROM DUAL
            CONNECT BY LEVEL <= 12
        ),
        INCOME_AGG AS (
            SELECT EXTRACT(MONTH FROM TRANSACTION_DATE) AS M_NUM,
                   NVL(SUM(AMOUNT), 0) AS INC_TOTAL
            FROM TRANSACTIONS
            WHERE USER_ID = p_user_id
              AND TRANSACTION_TYPE = 'INCOME'
              AND EXTRACT(YEAR FROM TRANSACTION_DATE) = v_target_year
            GROUP BY EXTRACT(MONTH FROM TRANSACTION_DATE)
        ),
        EXPENSE_AGG AS (
            SELECT EXTRACT(MONTH FROM TRANSACTION_DATE) AS M_NUM,
                   NVL(SUM(AMOUNT), 0) AS EXP_TOTAL
            FROM TRANSACTIONS
            WHERE USER_ID = p_user_id
              AND TRANSACTION_TYPE = 'EXPENSE'
              AND EXTRACT(YEAR FROM TRANSACTION_DATE) = v_target_year
            GROUP BY EXTRACT(MONTH FROM TRANSACTION_DATE)
        )
        SELECT 
            m.M_NUM               AS MONTH_NUM,
            m.M_NAME              AS MONTH_NAME,
            NVL(i.INC_TOTAL, 0)   AS TOTAL_INCOME,
            NVL(e.EXP_TOTAL, 0)   AS TOTAL_EXPENSE,
            (NVL(i.INC_TOTAL, 0) - NVL(e.EXP_TOTAL, 0)) AS NET_SAVINGS
        FROM MONTHS m
        LEFT JOIN INCOME_AGG i  ON m.M_NUM = i.M_NUM
        LEFT JOIN EXPENSE_AGG e ON m.M_NUM = e.M_NUM
        ORDER BY m.M_NUM;
END GET_MONTHLY_SUMMARY;
/

-- 7. GET_CATEGORY_SUMMARY: Retrieve category-wise expense totals as a SYS_REFCURSOR
CREATE OR REPLACE PROCEDURE GET_CATEGORY_SUMMARY (
    p_user_id IN  NUMBER,
    p_year    IN  NUMBER DEFAULT NULL,
    p_month   IN  NUMBER DEFAULT NULL,
    p_cursor  OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_cursor FOR
        SELECT 
            c.CATEGORY_NAME,
            c.CATEGORY_TYPE,
            NVL(SUM(t.AMOUNT), 0) AS TOTAL_AMOUNT,
            COUNT(t.TRANSACTION_ID) AS TRANSACTION_COUNT
        FROM CATEGORIES c
        JOIN TRANSACTIONS t ON c.CATEGORY_ID = t.CATEGORY_ID
        WHERE t.USER_ID = p_user_id
          AND t.TRANSACTION_TYPE = 'EXPENSE'
          AND (p_year IS NULL OR EXTRACT(YEAR FROM t.TRANSACTION_DATE) = p_year)
          AND (p_month IS NULL OR EXTRACT(MONTH FROM t.TRANSACTION_DATE) = p_month)
        GROUP BY c.CATEGORY_NAME, c.CATEGORY_TYPE
        ORDER BY TOTAL_AMOUNT DESC;
END GET_CATEGORY_SUMMARY;
/

-- 8. SAVE_BUDGET: Insert or update a budget (Upsert)
CREATE OR REPLACE PROCEDURE SAVE_BUDGET (
    p_user_id         IN  NUMBER,
    p_category_id     IN  NUMBER, -- NULL for overall monthly budget
    p_budget_month    IN  NUMBER,
    p_budget_year     IN  NUMBER,
    p_budget_amount   IN  NUMBER,
    p_alert_threshold IN  NUMBER,
    p_budget_id       OUT NUMBER
) AS
    v_existing_id NUMBER;
BEGIN
    IF p_budget_amount <= 0 THEN
        RAISE_APPLICATION_ERROR(-20003, 'Budget amount must be strictly greater than zero.');
    END IF;

    IF p_budget_month < 1 OR p_budget_month > 12 THEN
        RAISE_APPLICATION_ERROR(-20004, 'Budget month must be between 1 and 12.');
    END IF;

    -- Check if budget already exists for this scope
    BEGIN
        SELECT BUDGET_ID INTO v_existing_id
        FROM BUDGETS
        WHERE USER_ID = p_user_id
          AND BUDGET_YEAR = p_budget_year
          AND BUDGET_MONTH = p_budget_month
          AND ( (p_category_id IS NULL AND CATEGORY_ID IS NULL) OR CATEGORY_ID = p_category_id );
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            v_existing_id := NULL;
    END;

    IF v_existing_id IS NOT NULL THEN
        -- Update existing budget
        UPDATE BUDGETS
        SET BUDGET_AMOUNT   = ROUND(p_budget_amount, 2),
            ALERT_THRESHOLD = NVL(p_alert_threshold, 80)
        WHERE BUDGET_ID = v_existing_id;
        p_budget_id := v_existing_id;
    ELSE
        -- Insert new budget
        INSERT INTO BUDGETS (
            USER_ID,
            CATEGORY_ID,
            BUDGET_MONTH,
            BUDGET_YEAR,
            BUDGET_AMOUNT,
            ALERT_THRESHOLD,
            CREATED_AT
        ) VALUES (
            p_user_id,
            p_category_id,
            p_budget_month,
            p_budget_year,
            ROUND(p_budget_amount, 2),
            NVL(p_alert_threshold, 80),
            SYSDATE
        ) RETURNING BUDGET_ID INTO p_budget_id;
    END IF;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SAVE_BUDGET;
/

-- 9. GET_BUDGET_STATUS: Retrieve allocated budget, actual spending, remaining, utilization & alerts
CREATE OR REPLACE PROCEDURE GET_BUDGET_STATUS (
    p_user_id      IN  NUMBER,
    p_budget_year  IN  NUMBER,
    p_budget_month IN  NUMBER,
    p_cursor       OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_cursor FOR
        WITH ACTUAL_SPEND AS (
            SELECT 
                CATEGORY_ID,
                NVL(SUM(AMOUNT), 0) AS SPENT_AMOUNT
            FROM TRANSACTIONS
            WHERE USER_ID = p_user_id
              AND TRANSACTION_TYPE = 'EXPENSE'
              AND EXTRACT(YEAR FROM TRANSACTION_DATE) = p_budget_year
              AND EXTRACT(MONTH FROM TRANSACTION_DATE) = p_budget_month
            GROUP BY CATEGORY_ID
        ),
        TOTAL_MONTH_SPEND AS (
            SELECT NVL(SUM(AMOUNT), 0) AS OVERALL_SPENT
            FROM TRANSACTIONS
            WHERE USER_ID = p_user_id
              AND TRANSACTION_TYPE = 'EXPENSE'
              AND EXTRACT(YEAR FROM TRANSACTION_DATE) = p_budget_year
              AND EXTRACT(MONTH FROM TRANSACTION_DATE) = p_budget_month
        )
        SELECT 
            b.BUDGET_ID,
            b.CATEGORY_ID,
            NVL(c.CATEGORY_NAME, 'OVERALL MONTHLY BUDGET') AS CATEGORY_NAME,
            b.BUDGET_AMOUNT,
            CASE 
                WHEN b.CATEGORY_ID IS NULL THEN tms.OVERALL_SPENT
                ELSE NVL(asp.SPENT_AMOUNT, 0)
            END AS ACTUAL_SPENDING,
            (b.BUDGET_AMOUNT - CASE 
                WHEN b.CATEGORY_ID IS NULL THEN tms.OVERALL_SPENT
                ELSE NVL(asp.SPENT_AMOUNT, 0)
            END) AS REMAINING_BUDGET,
            ROUND((CASE 
                WHEN b.CATEGORY_ID IS NULL THEN tms.OVERALL_SPENT
                ELSE NVL(asp.SPENT_AMOUNT, 0)
            END / NULLIF(b.BUDGET_AMOUNT, 0)) * 100, 2) AS UTILIZATION_PCT,
            b.ALERT_THRESHOLD,
            CASE
                WHEN (CASE 
                        WHEN b.CATEGORY_ID IS NULL THEN tms.OVERALL_SPENT
                        ELSE NVL(asp.SPENT_AMOUNT, 0)
                      END) > b.BUDGET_AMOUNT THEN 'EXCEEDED'
                WHEN ROUND((CASE 
                        WHEN b.CATEGORY_ID IS NULL THEN tms.OVERALL_SPENT
                        ELSE NVL(asp.SPENT_AMOUNT, 0)
                      END / NULLIF(b.BUDGET_AMOUNT, 0)) * 100, 2) >= b.ALERT_THRESHOLD THEN 'WARNING'
                ELSE 'OK'
            END AS ALERT_STATUS
        FROM BUDGETS b
        CROSS JOIN TOTAL_MONTH_SPEND tms
        LEFT JOIN CATEGORIES c ON b.CATEGORY_ID = c.CATEGORY_ID
        LEFT JOIN ACTUAL_SPEND asp ON b.CATEGORY_ID = asp.CATEGORY_ID
        WHERE b.USER_ID = p_user_id
          AND b.BUDGET_YEAR = p_budget_year
          AND b.BUDGET_MONTH = p_budget_month
        ORDER BY CASE WHEN b.CATEGORY_ID IS NULL THEN 0 ELSE 1 END, b.BUDGET_AMOUNT DESC;
END GET_BUDGET_STATUS;
/
