import unittest
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.categories import Category, CategoryStatus, CategoryType
from app.models.transactions import Transaction, TransactionType
from app.models.users import User
from app.services.auth import create_access_token, get_current_user
from app.services.statistics import get_statistics
from app.services.transactions import list_transactions


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(email="owner@example.com")
        self.other_user = User(email="other@example.com")
        self.expense = Category(name="Food", type=CategoryType.EXPENSE)
        self.income = Category(name="Salary", type=CategoryType.INCOME)
        self.empty = Category(name="Unused", type=CategoryType.EXPENSE, status=CategoryStatus.INACTIVE)
        self.db.add_all([self.user, self.other_user, self.expense, self.income, self.empty])
        self.db.flush()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def add_transaction(self, user, category, kind, amount, when):
        self.db.add(Transaction(
            user_id=user.id,
            category_id=category.id if category else None,
            transaction_id=str(uuid4()),
            transaction_type=kind,
            amount=Decimal(amount),
            transaction_date=when,
        ))

    def test_totals_categories_and_filters(self):
        self.add_transaction(self.user, self.expense, TransactionType.DEBIT, "12.50", date(2026, 10, 1))
        self.add_transaction(self.user, self.income, TransactionType.CREDIT, "100.00", date(2026, 10, 31))
        self.add_transaction(self.user, None, TransactionType.DEBIT, "2.00", date(2026, 10, 15))
        self.add_transaction(self.user, self.expense, TransactionType.DEBIT, "9.00", date(2026, 9, 30))
        self.add_transaction(self.other_user, self.expense, TransactionType.DEBIT, "50.00", date(2026, 10, 15))
        self.db.flush()

        response = get_statistics(self.db, self.user.id, date(2026, 10, 1), date(2026, 10, 31))
        data = response.data

        self.assertEqual(data.total_expense, Decimal("14.50"))
        self.assertEqual(data.total_income, Decimal("100.00"))
        self.assertIsInstance(data.categories, list)
        categories = {item.category_id: item for item in data.categories}
        self.assertEqual(categories[self.expense.id].name, "Food")
        self.assertEqual(categories[self.expense.id].count, 1)
        self.assertEqual(len(categories[self.income.id].transactions), 1)
        self.assertIsNone(categories[self.empty.id].count)
        self.assertIsNone(categories[self.empty.id].transactions)
        self.assertEqual(categories[None].name, "Unknown")
        self.assertEqual(categories[None].count, 1)
        self.assertEqual(categories[None].transactions[0].category.category_name, "Unknown")
        self.assertEqual(len(data.categories), 4)
        serialized_categories = json.loads(response.model_dump_json())["data"]["categories"]
        self.assertIsInstance(serialized_categories, list)
        self.assertEqual(serialized_categories[0]["name"], "Food")
        self.assertEqual(serialized_categories[-1]["name"], "Unknown")

    def test_unknown_absent_without_uncategorized_transactions(self):
        data = get_statistics(self.db, self.user.id, date(2026, 10, 1), date(2026, 10, 31)).data
        self.assertEqual(len(data.categories), 3)
        self.assertNotIn("Unknown", [category.name for category in data.categories])

    def test_recent_transfer_date_stays_first_after_older_transaction_is_updated(self):
        older = Transaction(
            user_id=self.user.id, category_id=self.expense.id, transaction_id="older",
            transaction_type=TransactionType.DEBIT, amount=Decimal("1.00"),
            transaction_date=date(2026, 11, 1),
            updated_at=datetime(2026, 11, 9, tzinfo=timezone.utc),
        )
        newer = Transaction(
            user_id=self.user.id, category_id=self.expense.id, transaction_id="newer",
            transaction_type=TransactionType.DEBIT, amount=Decimal("2.00"),
            transaction_date=date(2026, 11, 8),
            updated_at=datetime(2026, 11, 8, tzinfo=timezone.utc),
        )
        self.db.add_all([older, newer])
        self.db.flush()

        self.assertEqual(
            [item.transaction_id for item in list_transactions(self.db, self.user.id)],
            ["newer", "older"],
        )
        categories = get_statistics(self.db, self.user.id, date(2026, 11, 1), date(2026, 11, 9)).data.categories
        expense = next(category for category in categories if category.category_id == self.expense.id)
        self.assertEqual([item.transaction_id for item in expense.transactions], ["newer", "older"])

    def test_rejects_reversed_dates(self):
        with self.assertRaises(HTTPException) as error:
            get_statistics(self.db, self.user.id, date(2026, 10, 31), date(2026, 10, 1))
        self.assertEqual(error.exception.status_code, 400)

    def test_authentication_uses_token_identity(self):
        with self.assertRaises(HTTPException) as missing_token:
            get_current_user(token=None, auth_token=None, db=self.db)
        self.assertEqual(missing_token.exception.status_code, 401)

        with self.assertRaises(HTTPException) as invalid_token:
            get_current_user(token="invalid", auth_token=None, db=self.db)
        self.assertEqual(invalid_token.exception.status_code, 401)

        token = create_access_token(self.user.id)
        self.assertEqual(get_current_user(token=token, auth_token=None, db=self.db).id, self.user.id)
        self.assertEqual(get_current_user(token=None, auth_token=token, db=self.db).id, self.user.id)


if __name__ == "__main__":
    unittest.main()
