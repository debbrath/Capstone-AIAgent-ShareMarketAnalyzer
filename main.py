from utils.config import build_connection_string
from utils.database_manager import DatabaseManager
from services.testdb import EmployeeService

def main():
    # Step 1: Build connection string
    connection_string = build_connection_string()
    print("🔗 Connection String:", connection_string)

    # Step 2: Initialize DB
    db_manager = DatabaseManager(connection_string)

    # Step 3: Create Service
    service = EmployeeService(db_manager)

    # Step 4: Ask for input
    emp_id = input("Enter Employee ID: ")
    result = service.get_employee_name(emp_id)

    # Step 5: Print output
    if result:
        print("🎯 Employee Info:", dict(result))
    else:
        print("❌ No record found.")

if __name__ == "__main__":
    main()