import unittest
from unittest.mock import patch
from datetime import datetime
from math import log
from .decroissance import DecroissanceDialog
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication
import sys

# filepath: src/fonctions/test_decroissance.py


class TestDecroissanceCalculator(unittest.TestCase):
    def setUp(self):
        # Create QApplication instance if not exists
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        self.calculator = DecroissanceDialog()

    @patch('datetime.datetime')
    def test_activity_halved_after_one_period(self, mock_datetime):
        """Test that activity is halved after one half-life period"""
        # Setup
        initial_activity = 1000  # Bq
        period_seconds = 3600  # 1 hour
        
        # Mock current time to be exactly one period after start
        start_date = datetime(2023, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 1, 0, 0)  # 1 hour later
        
        self.calculator.activity_input.setValue(initial_activity)
        self.calculator.activity_unit.setCurrentText("Bq")
        self.calculator.period_seconds = period_seconds
        self.calculator.date_input.setDate(QDate(2023, 1, 1))
        
        # Execute
        self.calculator.calculate_decay()
        
        # Assert - activity should be halved after one period
        result_bq = float(self.calculator.result_bq_label.text().split()[0])
        self.assertAlmostEqual(result_bq, initial_activity/2, places=2)

    @patch('datetime.datetime')
    def test_activity_quartered_after_two_periods(self, mock_datetime):
        """Test that activity is reduced to 1/4 after two half-life periods"""
        # Setup
        initial_activity = 1000  # Bq
        period_seconds = 3600  # 1 hour
        
        # Mock current time to be exactly two periods after start
        start_date = datetime(2023, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 2, 0, 0)  # 2 hours later
        
        self.calculator.activity_input.setValue(initial_activity)
        self.calculator.activity_unit.setCurrentText("Bq")
        self.calculator.period_seconds = period_seconds
        self.calculator.date_input.setDate(QDate(2023, 1, 1))
        
        # Execute
        self.calculator.calculate_decay()
        
        # Assert - activity should be 1/4 after two periods
        result_bq = float(self.calculator.result_bq_label.text().split()[0])
        self.assertAlmostEqual(result_bq, initial_activity/4, places=2)

    @patch('datetime.datetime')
    def test_unit_conversion(self, mock_datetime):
        """Test that unit conversions are handled correctly"""
        # Setup
        initial_activity = 1  # GBq = 1e9 Bq
        period_seconds = 3600  # 1 hour
        
        # Mock current time to be exactly one period after start
        start_date = datetime(2023, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 1, 0, 0)  # 1 hour later
        
        self.calculator.activity_input.setValue(initial_activity)
        self.calculator.activity_unit.setCurrentText("GBq")
        self.calculator.period_seconds = period_seconds
        self.calculator.date_input.setDate(QDate(2023, 1, 1))
        
        # Execute
        self.calculator.calculate_decay()
        
        # Assert - activity should be halved after one period
        result_gbq = float(self.calculator.result_gbq_label.text().split()[0])
        self.assertAlmostEqual(result_gbq, 0.5, places=2)  # 0.5 GBq expected

    def test_no_period_set(self):
        """Test that calculation requires a period to be set"""
        # Setup
        self.calculator.period_seconds = 0
        self.calculator.activity_input.setValue(1000)
        
        # Execute & Assert
        with self.assertRaises(Exception):
            self.calculator.calculate_decay()

if __name__ == '__main__':
    unittest.main()