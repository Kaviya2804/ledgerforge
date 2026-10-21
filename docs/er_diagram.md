erDiagram
    DEPARTMENTS ||--o{ ROLES : contains
    DEPARTMENTS ||--o{ EMPLOYEES : has
    ROLES ||--o{ EMPLOYEES : assigned_to

    EMPLOYEES ||--o{ EMPLOYEE_ASSIGNMENTS : has_history
    DEPARTMENTS ||--o{ EMPLOYEE_ASSIGNMENTS : records
    ROLES ||--o{ EMPLOYEE_ASSIGNMENTS : records

    EMPLOYEES o|--o{ EMPLOYEES : manages
    EMPLOYEES o|--o{ EMPLOYEE_ASSIGNMENTS : manages

    DEPARTMENTS {
        string department_id PK
        string department_name
        string cost_center
        string description
    }

    ROLES {
        string role_id PK
        string department_id FK
        string role_title
        int level
        string grade
        decimal band_min_annual
        decimal band_mid_annual
        decimal band_max_annual
        boolean overtime_eligible
        int band_year
    }

    EMPLOYEES {
        string emp_id PK
        string fname
        string lname
        string full_name
        string work_email
        date dob
        date hire_date
        date exit_date
        string department_id FK
        string role_id FK
        string manager_id FK
    }

    EMPLOYEE_ASSIGNMENTS {
        string assignment_id PK
        string employee_id FK
        date effective_from
        date effective_to
        string department_id FK
        string role_id FK
        string manager_id FK
        int job_level
        string change_reason
    }

    ## Nullable Columns

1. The department description can be NULL because a description may not always be available.

2. The employee manager_id can be NULL when an employee does not have a manager assigned or the manager information is unavailable.

3. The employee exit_date and assignment effective_to can be NULL because an employee may still be working and an assignment may still be active.