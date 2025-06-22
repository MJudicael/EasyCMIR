from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QGroupBox, QDoubleSpinBox,
    QLabel, QComboBox
)

class PIDDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PID")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Groupe mesure
        measure_group = QGroupBox("Mesure PID")
        measure_layout = QHBoxLayout()
        measure_group.setLayout(measure_layout)
        
        # Zone de saisie
        self.value_input = QDoubleSpinBox()
        self.value_input.setRange(0, 100000)
        self.value_input.setDecimals(1)
        self.value_input.setSuffix(" ppm")
        
        measure_layout.addWidget(QLabel("Valeur :"))
        measure_layout.addWidget(self.value_input)
        
        # Boutons
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        # Assemblage
        layout.addWidget(measure_group)
        layout.addLayout(btn_layout)