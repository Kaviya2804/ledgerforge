# Task 13 – Security Test Report

## LedgerForge – Authentication and Role-Based Access Control

### 1. Authentication Tests

| Test | Expected Result | Actual Result |
|---|---|---|
| ADMIN login | 200 OK | PASS |
| HR login | 200 OK | PASS |
| EMPLOYEE login | 200 OK | PASS |
| Access without token | 401 Unauthorized | PASS |

### 2. Role-Based Access Tests

| Test | Expected Result | Actual Result |
|---|---|---|
| EMPLOYEE accesses employee list | 403 Forbidden | PASS |
| EMPLOYEE accesses departments | 403 Forbidden | PASS |
| EMPLOYEE accesses another employee's profile | 403 Forbidden | PASS |
| EMPLOYEE accesses another employee's salary | 403 Forbidden | PASS |
| EMPLOYEE accesses another employee's payslip | 403 Forbidden | PASS |

### 3. Employee Self-Access Tests

| Test | Expected Result | Actual Result |
|---|---|---|
| Employee accesses own profile | 200 OK | PASS |
| Employee accesses own salary | 200 OK | PASS |
| Employee accesses own payslip | 200 OK | PASS |

### 4. Account Deactivation Test

- Generated a valid access token for an active employee.
- Deactivated the employee account in a separate test database.
- Tried accessing the application using the existing token.
- Existing token was rejected.

**Expected Result:** 401 Unauthorized

**Actual Result:** 401 Unauthorized

**Status:** PASS

### 5. Security Implementation

- Passwords stored using bcrypt hashing.
- JWT authentication implemented.
- Access token validity: 30 minutes.
- Secret key loaded from environment variables.
- Role-based authorization implemented.
- Inactive users blocked from using existing tokens.
- Employee access restricted to their own profile, salary and payslip.

### 6. Conclusion

Authentication, role-based access control, employee data privacy and account deactivation tests were successfully completed for Task 13.
