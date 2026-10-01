"""Read-only invoice queries for verified customers."""

from functools import lru_cache

from ..database import ChinookRepository, get_engine_for_chinook_db


@lru_cache(maxsize=1)
def _repository() -> ChinookRepository:
    return ChinookRepository(get_engine_for_chinook_db())


def get_invoices_by_customer_sorted_by_date(customer_id: str):
    """Retrieve a customer's invoices, most recent first."""
    return _repository().fetch_all(
        """
        SELECT InvoiceId AS invoice_id, InvoiceDate AS invoice_date, Total AS total
        FROM Invoice
        WHERE CustomerId = :customer_id
        ORDER BY datetime(InvoiceDate) DESC
        """,
        {"customer_id": int(customer_id)},
    )


def get_invoices_sorted_by_unit_price(customer_id: str):
    """Retrieve a customer's invoice lines, highest unit price first."""
    return _repository().fetch_all(
        """
        SELECT i.InvoiceId AS invoice_id, i.InvoiceDate AS invoice_date,
               t.Name AS track, il.UnitPrice AS unit_price, il.Quantity AS quantity
        FROM Invoice AS i
        JOIN InvoiceLine AS il ON il.InvoiceId = i.InvoiceId
        JOIN Track AS t ON t.TrackId = il.TrackId
        WHERE i.CustomerId = :customer_id
        ORDER BY il.UnitPrice DESC, i.InvoiceId DESC
        """,
        {"customer_id": int(customer_id)},
    )


def get_employee_by_invoice_and_customer(invoice_id: str, customer_id: str):
    """Retrieve the support employee associated with an invoice and customer."""
    return _repository().fetch_one(
        """
        SELECT e.EmployeeId AS employee_id, e.FirstName AS first_name,
               e.LastName AS last_name, e.Email AS email
        FROM Invoice AS i
        JOIN Customer AS c ON c.CustomerId = i.CustomerId
        JOIN Employee AS e ON e.EmployeeId = c.SupportRepId
        WHERE i.InvoiceId = :invoice_id AND i.CustomerId = :customer_id
        """,
        {"invoice_id": int(invoice_id), "customer_id": int(customer_id)},
    )