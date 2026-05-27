import pytest
from app.services.query import QueryService
from app.core.exceptions import QueryValidationError

# Mock DB objects since validator is pure AST logic
def test_sql_validator_allowed_queries():
    service = QueryService(db=None, ro_db=None)
    
    # Standard SELECT queries should not raise exceptions
    service.validate_sql_safety("SELECT * FROM biz_customers;")
    service.validate_sql_safety("SELECT name, email FROM biz_customers WHERE city = 'Mumbai';")
    service.validate_sql_safety("SELECT c.name, SUM(o.amount) FROM biz_customers c JOIN biz_payments o USING(customer_id) GROUP BY c.name;")

def test_sql_validator_blocked_queries():
    service = QueryService(db=None, ro_db=None)
    
    # Mutating actions should raise validation errors
    with pytest.raises(Exception):
        service.validate_sql_safety("DROP TABLE biz_customers;")
        
    with pytest.raises(Exception):
        service.validate_sql_safety("DELETE FROM biz_customers WHERE id = 1;")
        
    with pytest.raises(Exception):
        service.validate_sql_safety("UPDATE biz_customers SET name = 'Hacker';")
        
    with pytest.raises(Exception):
        service.validate_sql_safety("INSERT INTO biz_customers (name) VALUES ('Hacker');")
