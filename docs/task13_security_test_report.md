# Task 13 – Security Test Report
## LedgerForge: Authentication and Role-Based Access Control

### 1. Objective

Implemented authentication and role-based access control (RBAC) to protect employee, salary and payroll information.

### 2. Implementation Summary

- Created the users database table.
- Loaded 745 demo users from the users data.
- Stored passwords using bcrypt hashing.
- Implemented JWT-based authentication.
- Configured access tokens to expire after 30 minutes.
- Loaded the secret key from environment configuration.
- Created reusable `get_current_user` and `require_roles` security dependencies.
- Protected API endpoints based on user roles.
- Restricted employees to their own profile, salary and payslip information.
- Rejected existing tokens belonging to deactivated users.

### 3. User Roles

| Role | Permissions |
|---|---|
| ADMIN | Manage and access employee, department, salary and payslip information |
| HR | Access employee, department, salary and payslip information |
| EMPLOYEE | Access only their own profile, salary and payslips |

### 4. Route-Wise Role Permission Table

| HTTP Method | API Endpoint | ADMIN | HR | EMPLOYEE |
|---|---|---|---|---|
| POST | /auth/login | Public | Public | Public |
| GET | /departments | Yes | Yes | No |
| GET | /departments/{department_id} | Yes | Yes | No |
| GET | /employees/ | Yes | Yes | No |
| GET | /employees/{emp_id} | Any employee | Any employee | Own profile only |
| POST | /employees/ | Yes | Yes | No |
| PATCH | /employees/{emp_id} | Yes | Yes | No |
| DELETE | /employees/{emp_id} | Yes | Yes | No |
| GET | /employees/{emp_id}/team | Yes | Yes | No |
| GET | /salary/{employee_id}/structure | Any employee | Any employee | Own salary only |
| GET | /salary/{employee_id}/history | Any employee | Any employee | Own salary only |
| GET | /payslips/{employee_id}/{run_id} | Any employee | Any employee | Own payslips only |

Note: `/health` is a public health-check endpoint.

### 5. Authentication and Authorization Tests

| Test Case | Expected Result | Actual Result |
|---|---|---|
| Access employees endpoint without token | 401 Unauthorized | Passed |
| Employee accesses employees list | 403 Forbidden | Passed |
| Employee accesses departments | 403 Forbidden | Passed |
| Employee accesses another employee profile | 403 Forbidden | Passed |
| Employee accesses another employee salary | 403 Forbidden | Passed |
| Employee accesses another employee payslip | 403 Forbidden | Passed |
| Employee accesses own profile | 200 OK | Passed |
| Employee accesses own salary | 200 OK | Passed |
| Employee accesses own payslip | 200 OK | Passed |

### 6. Password Security

- Passwords are hashed using bcrypt.
- Plaintext passwords are not stored in the users table.
- Password verification is performed during login.

### 7. JWT Token Security

- JWT tokens use HS256 signing.
- Token expiration is configured for 30 minutes.
- The secret key is loaded from environment settings.
- Protected endpoints validate the token and current user status.

### 8. Deactivated User Test

Test scenario: A user is deactivated while holding an already generated valid JWT token.

Test results:

- Token generated: SUCCESS
- User active before deactivation: True
- User active after deactivation: False
- Existing token rejected: PASSED
- Response status: 401 Unauthorized

Conclusion: Deactivated users cannot continue accessing protected endpoints using previously generated tokens.

### 9. Security Test Summary

- Authentication tests: Passed.
- Role-based authorization tests: Passed.
- Employee data privacy tests: Passed.
- Password hashing verification: Passed.
- JWT expiration configuration: Implemented.
- Deactivated user token test: Passed.

Complete project test suite: 40 passed.

### 10. GitHub Reference Links

Project Repository:
https://github.com/Kaviya2804/ledgerforge

Branch:
lf-02-employee-model

Security implementation references:

- bcrypt: https://github.com/pyca/bcrypt
- PyJWT: https://github.com/jpadilla/pyjwt
- FastAPI: https://github.com/fastapi/fastapi

### 11. Conclusion

Task 13 authentication and role-based access control were implemented and tested successfully.

The LedgerForge API now uses password hashing, JWT authentication, token expiration and role-based permissions to protect employee and payroll information.

All recorded security tests passed.
