"""
Query Service and NL-to-SQL Engine orchestrator.
Translates user natural language questions into safe SQL, validates, executes,
and returns structured data summaries and Chart configurations.
"""

from __future__ import annotations

import time
import structlog
import sqlglot
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import get_settings
from app.core.exceptions import SQLGenerationError, QueryValidationError, QueryExecutionError
from app.database.repositories.conversation import ConversationRepository
from app.schemas.query import QueryResponse, ChartConfig, ChartType
from app.services.gemini import GeminiClient

logger = structlog.get_logger(__name__)
settings = get_settings()

# Simple in-memory cache for frequently run queries
_query_cache: dict[str, QueryResponse] = {}

class QueryService:
    def __init__(self, db: AsyncSession, ro_db: AsyncSession) -> None:
        self.db = db
        self.ro_db = ro_db
        self.convo_repo = ConversationRepository(db)
        self.gemini = GeminiClient()

    async def execute_nl_query(self, user_id: UUID, question: str, session_id: UUID | None = None) -> QueryResponse:
        """
        Processes a natural language question by:
        0. Running SchemaWatcher check for real-time catalog changes
        1. Checking the query cache memory
        2. Classifying intent and schema context
        3. Generating the SQL query
        ...
        """
        # Run Real-Time Schema Watcher Check
        try:
            from app.services.nlsql.schema_watcher import SchemaWatcher
            watcher = SchemaWatcher(self.db)
            if await watcher.check_for_updates():
                logger.warning("query_service.schema_ddl_change_detected", 
                               message="Schema catalogs changed! Invalidating query cache.")
                _query_cache.clear()
        except Exception as we:
            logger.error("query_service.watcher_failed", error=str(we))

        # Check Cache Memory for most frequent queries
        cache_key = question.strip().lower()
        if cache_key in _query_cache:
            logger.info("query_service.cache_hit", question=question)
            return _query_cache[cache_key]

        session_id = session_id or uuid4()
        start_time = time.perf_counter()


        
        # 1. Intent classifier & Schema selection (based on search terms)
        intent = "general"
        question_lower = question.lower()
        if "sales" in question_lower or "revenue" in question_lower or "spent" in question_lower or "amount" in question_lower:
            intent = "sales"
        elif "customer" in question_lower or "user" in question_lower:
            intent = "customers"
        elif "product" in question_lower or "category" in question_lower or "items" in question_lower or "brand" in question_lower:
            intent = "inventory"

        # Schema details to supply context to the model
        schema_context = """
        biz_customers (
            customer_id UUID PRIMARY KEY,
            name VARCHAR(150),
            email VARCHAR(255) UNIQUE,
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            segment VARCHAR(50) -- 'Consumer', 'Corporate', 'Home Office'
        );
        biz_products (
            product_id UUID PRIMARY KEY,
            name VARCHAR(255),
            category VARCHAR(100),
            sub_category VARCHAR(100),
            price NUMERIC(12, 2),
            cost NUMERIC(12, 2),
            brand VARCHAR(100)
        );
        biz_orders (
            order_id UUID PRIMARY KEY,
            customer_id UUID REFERENCES biz_customers(customer_id),
            order_date DATE,
            ship_date DATE,
            ship_mode VARCHAR(50),
            status VARCHAR(50) -- 'Pending', 'Shipped', 'Delivered', 'Returned', 'Cancelled'
        );
        biz_order_items (
            item_id UUID PRIMARY KEY,
            order_id UUID REFERENCES biz_orders(order_id),
            product_id UUID REFERENCES biz_products(product_id),
            quantity INTEGER,
            unit_price NUMERIC(12, 2),
            discount NUMERIC(5, 2)
        );
        biz_payments (
            payment_id UUID PRIMARY KEY,
            order_id UUID REFERENCES biz_orders(order_id),
            payment_method VARCHAR(50), -- 'Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'COD'
            amount NUMERIC(12, 2),
            status VARCHAR(50), -- 'Pending', 'Completed', 'Failed', 'Refunded'
            paid_at DATETIME
        );
        """

        prompt = f"""
        You are an expert PostgreSQL and SQLite business intelligence analyst. Generate ONLY a single SQL query matching the schema.

        DATABASE SCHEMA:
        {schema_context}

        BUSINESS RULES:
        - Revenue/spent = SUM(quantity * unit_price * (1 - discount/100))
        - Profit = Revenue - cost (quantity * cost)
        - Use simple date formats.

        USER QUESTION: {question}

        RULES:
        1. Output ONLY valid standard SQL — no markdown, no explanation, no formatting blocks.
        2. Use only tables and columns from the schema above.
        3. Do NOT use PostgreSQL specific functions if standard SQL can do it (e.g. date_trunc can use strftime or formatting for SQLite fallback).
        4. Limit output results to 1000 rows.
        """

        # 2. SQL Generation
        generated_sql = await self.gemini.generate_sql(prompt)
        
        # Fallback to local default query structures if Gemini API client isn't fully configured
        if not self.gemini.client:
            if intent == "sales":
                generated_sql = "SELECT order_date as date, SUM(amount) as revenue FROM biz_orders JOIN biz_payments USING (order_id) GROUP BY 1 ORDER BY 1;"
            elif intent == "customers":
                generated_sql = "SELECT name, SUM(quantity * unit_price) as spent FROM biz_customers JOIN biz_orders USING (customer_id) JOIN biz_order_items USING (order_id) GROUP BY 1 ORDER BY 2 DESC;"
            elif intent == "inventory":
                generated_sql = "SELECT category, count(*) as items_sold FROM biz_products JOIN biz_order_items USING (product_id) GROUP BY 1 ORDER BY 2 DESC;"
            else:
                generated_sql = "SELECT 'System Operational' as status, date() as current_date;"

        # 3. SQL Safety Validation (SQLGlot AST Parsing)
        try:
            self.validate_sql_safety(generated_sql)
        except Exception as ve:
            logger.error("query.validation_error", sql=generated_sql, error=str(ve))
            # Safe local fallback on validation failure
            generated_sql = "SELECT 'Safety Fallback' as status;"

        columns = []
        rows = []
        error_msg = None
        execution_start = time.perf_counter()

        # 4. Database Query Execution
        try:
            result = await self.ro_db.execute(text(generated_sql))
            columns = list(result.keys())
            rows = [list(r) for r in result.fetchall()]
        except Exception as e:
            logger.error("query.execution_error", sql=generated_sql, error=str(e))
            error_msg = str(e)
            columns = ["error"]
            rows = [[error_msg]]

        execution_time_ms = (time.perf_counter() - execution_start) * 1000

        # Convert query rows into dict preview format for LLM summary
        results_preview = [dict(zip(columns, r)) for r in rows[:10]]

        # 5. Result Summarization
        summary_result = await self.gemini.generate_summary(
            question=question,
            sql=generated_sql,
            results_preview=results_preview,
        )

        summary = summary_result.get("summary", "Query executed successfully.")
        chart_rec = summary_result.get("chart_recommendation", {})
        chart_type_str = chart_rec.get("chart_type", "none")
        
        # Map chart type safely
        try:
            chart_type = ChartType(chart_type_str)
        except ValueError:
            chart_type = ChartType.NONE

        chart_config = None
        if chart_type != ChartType.NONE and len(rows) > 0:
            x_col = chart_rec.get("x_column", columns[0] if len(columns) > 0 else "")
            y_col = chart_rec.get("y_column", columns[1] if len(columns) > 1 else "")
            
            # Safe indices check
            x_idx = columns.index(x_col) if x_col in columns else 0
            y_idx = columns.index(y_col) if y_col in columns else (1 if len(columns) > 1 else 0)

            chart_config = ChartConfig(
                chart_type=chart_type,
                labels=[str(row[x_idx]) for row in rows[:15]],  # Cap values to make visual rendering sleek
                datasets=[
                    {
                        "label": y_col.replace("_", " ").title(),
                        "data": [float(row[y_idx]) if isinstance(row[y_idx], (int, float, Decimal)) else 0 for row in rows[:15]],
                    }
                ],
                title=chart_rec.get("title", "Insight Chart"),
                x_label=x_col.replace("_", " ").title(),
                y_label=y_col.replace("_", " ").title(),
            )

        # Save query turn log to local database
        convo = await self.convo_repo.create_conversation(
            user_id=user_id,
            question=question,
            intent_category=intent,
            generated_sql=generated_sql,
            validated_sql=generated_sql,
            result_summary=summary,
            row_count=len(rows),
            execution_time_ms=execution_time_ms,
            response_text=summary,
            session_id=session_id,
            error_message=error_msg,
        )

        response = QueryResponse(
            id=convo.id,
            question=convo.question,
            intent=convo.intent_category,
            generated_sql=convo.generated_sql,
            columns=columns,
            rows=rows,
            row_count=convo.row_count,
            execution_time_ms=convo.execution_time_ms,
            summary=convo.result_summary,
            chart_config=chart_config,
            session_id=convo.session_id,
            created_at=convo.created_at,
        )
        
        # Save to cache memory (LRU cap could be added, here is simple dictionary indexing)
        _query_cache[cache_key] = response
        return response


    def validate_sql_safety(self, sql: str) -> None:
        """
        Validate SQL statements using SQLGlot AST structural parsing.
        """
        try:
            # Parse the SQL query into expressions
            expressions = sqlglot.parse(sql)
            for expression in expressions:
                if not expression:
                    continue
                # Traverse AST checking for mutating commands
                for node in expression.walk():
                    node_type = type(node).__name__.upper()
                    if any(bad in node_type for bad in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]):
                        raise QueryValidationError(f"Forbidden command detected in AST structures: {node_type}")
        except sqlglot.errors.ParseError as pe:
            # Fallback simple keyword containment check if sqlglot parsing fails due to dialect mismatches
            logger.warning("sqlglot.parse_failed_fallback_to_string_checks", error=str(pe))
            upper_sql = sql.upper()
            blocked = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE", "EXEC"]
            for keyword in blocked:
                if f" {keyword} " in f" {upper_sql} " or upper_sql.startswith(keyword):
                    raise QueryValidationError(f"Security Alert: Blocked keyword '{keyword}' found in statement.")
