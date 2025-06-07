from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextBrowser
import requests
from bs4 import BeautifulSoup

class NewsDialog(QDialog):
    """Dialog pour l'affichage des actualités ASN."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actualités ASN")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.layout = QVBoxLayout(self)
        
        # Zone de texte scrollable avec support des liens
        self.news_text = QTextBrowser()
        self.news_text.setOpenExternalLinks(True)
        self.layout.addWidget(self.news_text)
        
        # Bouton de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        self.layout.addWidget(close_button)
        
        # Chargement des news
        self.load_asn_news()
    
    def load_asn_news(self):
        try:
            self.news_text.setText("Chargement des actualités ASN...")
            
            # Récupération des news ASN
            page = requests.get("https://www.asnr.fr/actualites")
            soup = BeautifulSoup(page.content, 'html.parser')
            
            # On cherche les cartes d'actualités
            news_items = soup.find_all("div", class_="irsn-related-card")
            
            # Formatage des news en HTML avec liens
            news_html = "<h2>ACTUALITÉS ASNR:</h2>"
            
            for item in news_items:
                # Récupère le titre et le lien
                title_element = item.find("div", class_="irsn-related-card__title")
                link_element = item.find("a")
                
                if title_element and link_element:
                    title = title_element.get_text().strip()
                    # Le lien est relatif, on ajoute donc le domaine
                    link = "https://www.asnr.fr" + link_element.get('href', '')
                    
                    # Récupération de la date si disponible
                    date_element = item.find("div", class_="irsn-related-card__date")
                    date_text = date_element.get_text().strip() if date_element else ""
                    
                    news_html += f"""
                    <p style='margin-bottom: 10px;'>
                        • <a href='{link}' style='color: #004175; text-decoration: none;' target='_blank'>
                            {title}
                        </a>
                        <br><span style='font-size: 0.9em; color: #666;'>{date_text}</span>
                    </p>"""
            
            self.news_text.setHtml(news_html)
            
        except Exception as e:
            self.news_text.setText(f"Erreur lors du chargement des actualités:\n{str(e)}")